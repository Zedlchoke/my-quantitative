# m4 — FX-F4 r = RT/MDE re-derivation at the M2c-corrected reopen-gap scale (WORK_QUEUE A-#12 / HYPO G8)

- Lane **MEAS-FX**, round **FUTURES-5SYM-PRESCORED-20261005** wave-3.
- Binding consumption law of the M2c erratum (FXEB_K6_GATES §2 M2c): "any
  freeze re-derives first". This IS that re-derivation, as descriptive
  power/cost arithmetic. No PnL, no expectancy, no direction claim; no
  §4 refutation condition is adjudicated; nothing is scheduled; PB2 HOLD
  untouched. Machine mirror: `m4_fx_f4_rt_mde.json`. Generator:
  `meas_fx_m4_f4_rt_mde.py`.

## Inputs (all committed)

- Corrected 17:00-CT reopen-gap anatomy
  (`FUTURES-K6GATE-PREP-20261004/fx_eb/fx_f1_f4_census.json:
  fx_f4_reopen_gap.<SYM>`):

| stratum | 6E std | 6E n | 6B std | 6B n |
|---|---|---|---|---|
| BASE weekday reopens | 0.030382% (3.038 bp) | 1,282 | 0.039990% (3.999 bp) | 1,283 |
| BASE all pairs | 0.074129% (7.413 bp) | 1,599 | 0.080388% (8.039 bp) | 1,600 |
| Sunday stratum | 0.154534% (15.453 bp) | 317 | 0.161638% (16.164 bp) | 317 |

- Companion day-return std (same evaluable set): 6E 0.46374%, 6B 0.55127%
  ⇒ ratio gap/day = **0.1599 (6E) / 0.1458 (6B)** all-pairs (the "ratio
  ≈0.16" of HYPO G8; weekday-only 0.066/0.073) — versus the family doc's
  cited 0.805, which was the **08:30-CT RTH-open gap** (recorded baseline
  0.3778%, n=1,739; re-derived 0.3773% reproduces to the 4th decimal —
  the M2c mislabeling finding, consumed not overwritten).
- Weekday gap percentile band: 6E p05/p50/p95 = −3.364/0.000/+3.103 bp;
  6B = −4.5/+0.0/+4.404 bp (from the committed `gap_distribution_BASE_weekday`).
- Modeled RT floors (committed, MODELED / UNDER REVIEW, A7 outstanding):
  **6E 3.6–6.3 bp; 6B 6.3–11.2 bp** (FX_HYPOTHESES §2 shared block:
  fee 2.46 USD/side T1 + spread close-proxy $18.75/side high-biased +
  slippage {1,2,3} × $6.25/side). Component check (descriptive only,
  declared representative spots 1.16/1.34): RT USD 54.92–79.92 ⇒ 3.79–5.51
  bp (6E @ $14.50/bp) and 6.56–9.54 bp (6B @ $8.375/bp) — reproduces the
  committed ranges to rounding; the committed ranges are the authority.
- MDE formula (court §c3): MDE = 2.80 × σ / √n.

## Arithmetic

**Reading A — the committed MDE definition (daily-σ upper bound; the
§4.7 rows use exactly this — the LEAST corrected reading):**

| | σ (bp) | MDE @ census n | MDE @ doc n (1,573/1,572; §4.7 row 3.27/3.88) |
|---|---|---|---|
| 6E | 46.374 | 2.80×46.374/√1,282 = **3.628 bp** | 2.80×46.374/√1,573 = 3.273 bp ✓ |
| 6B | 55.127 | 2.80×55.127/√1,283 = **4.313 bp** | 3.894 bp ✓ |

r = RT/MDE @ census n: **6E 0.99–1.74; 6B 1.46–2.60** (@ doc n: 6E
1.10–1.92; 6B 1.62–2.88).

**Reading B — the corrected scale per this lane's dispatch (MDE from the
M2c-corrected gap std; premise-scale dispersion):**

| stratum | 6E MDE (bp) | r = RT/MDE | 6B MDE (bp) | r = RT/MDE |
|---|---|---|---|---|
| weekday base (n=1,282/1,283) | 2.80×3.038/35.805 = **0.2376** | **15.2–26.5** | 0.3126 | **20.2–35.8** |
| all pairs (n=1,599/1,600) | 0.5191 | 6.9–12.1 | 0.5627 | 11.2–19.9 |
| Sunday (n=317) | 2.4303 | 1.48–2.59 | 2.5420 | 2.48–4.41 |

**Scale bound (percentile check):** the p95 weekday reopen gap — an upper
proxy for the per-trade edge under FULL gap capture — is **+3.103 bp (6E)
vs RT floor 3.6 bp** and **+4.404 bp (6B) vs RT floor 6.3 bp**: below the
modeled cost floor on both legs for ≥90% of the base population.

## Verdict (power honesty)

**YES — FX-F4 dies at program-feasible n under the corrected scale, and
the conclusion is robust across every committed dispersion reading.**
Reading A (least corrected): r ≥ 1 everywhere except the single most
favorable cell (6E low tier 0.99 — an effect exactly at MDE nets ≈0 after
modeled cost). Reading B (corrected gap-std scale): r ≈ 15–36 weekday /
7–20 all-pairs / 1.5–4.4 Sunday — cost exceeds the detectable scale by
an order of magnitude. The p95 bound independently shows even full capture
of a 90th-percentile gap does not clear the RT floor.

Worsening directions (disclosed): any §4.5 minimum-gap threshold (a
registered-cycle decision) only lowers n ⇒ raises MDE ⇒ raises r; the
17:00-CT spread is disclosed as likely MOST biased-low (thinnest window,
p05 session volume 7,904) so the RT floor is more likely understated than
overstated; Sunday — the only stratum whose gap scale (15.5/16.2 bp)
exceeds RT — is a separate stratum at n=317 with r ≥ 1.48.

Caveats: all costs MODELED / UNDER REVIEW (A7); BBO NOT_RUN; per-trade F4
dispersion is NOT_RUN (conditional) — both readings are the committed
proxy constructions, not measured trade dispersion; 6B 0/42 holiday grid
NOT_OBTAINED stands fail-closed. No numeric threshold existed in any
owning doc; none invented here.

— End m4.
