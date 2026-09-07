# V9 D1 lane A6 — death-event structure proposals (blind)

- Cycle / wave: STOCKS-FREE-V9, wave SHA `86fecae8044d344e5d5ea9a49bbcfdb2f03c0b5a`
- Worktree: `.worktrees/stocks-free-v9/d1-a6-deathevent` (branch `orca/stocks-free-v9-d1-a6-deathevent`, base = wave SHA)
- Producer: A6, outcome-blind proposal lane. **No scored computation, no returns, no PnL exists or was computed.** All numbers below are Phase-P structure counts from frozen evidence and staged raw price bytes (no return is computed in Phase P).
- Deliverables: `a6_death_H1.json`, `a6_death_H2.json` (schema `stocks_free_v9_run/d1_proposal@1`), this README. One commit, explicit paths, no push.

## The two proposals

| | SFV9-A6-H1 — death-wave arrival | SFV9-A6-H2 — death-channel taxonomy |
|---|---|---|
| Conditioner | trailing 63-session count of active-series evidenced deaths (N63), expanding terciles | 12B-route minus 12G-route count of the same stream (P63), expanding terciles |
| Direction claim | high intensity → short dying cohort; low → long (fire-sale contagion vs consideration windows) | 12B-dominant → short (exchange-delisting channel); 12G-dominant → long (merger/going-private channel) |
| Arms | anchor 63w / neighbour 126w / **stale-63 control** (arrival content deleted, level kept) | anchor 63w / neighbour 126w / **label-swap control** (exact conditioner negation — a pure sign test of the taxonomy) |
| Scored decisions (measured) | 56 (11/18/27) | 64 (11/26/27) |
| Literature spine | Shumway 2001 hazard; Coval-Stafford fire sales; Nagel 2012 | Shumway-Warner 1999 reason bimodality; Macey-Netter-Szewczyk exchange exit |

Shared machinery (declared, for comparability): dead-leg-only universe (1,550 `DEAD_PRICE_CONFIRMED`), inherited 63+21k grid (80 decisions), inherited eligibility floors, one-sided equal-weight book per regime, next-session fills with the frozen fill-check, exit-at-last-close for series deaths, band costs with the preregistered band-D terminal-exit resolution (C-rate ceiling).

## Structure-only feasibility facts (measured, no returns)

From `death_census.json` (P0a), `p0d_v9_integrity_scan.json` (P0d), `cohort_v9.json` (P0b) and the sha-pinned staged EODHD series:

- Dead leg: 1,550 `DEAD_PRICE_CONFIRMED`. Last-trade vs filing: median −11d, p25 −20, p75 −5, p90 +7; 1,349 series end ON/BEFORE the filing date (the OTC tail does not exist in the served data).
- **Event stream**: 1,550 cohort deaths; 1,246 pass the active-series filter (name traded within 63 sessions before its filing); type mix among active: 776 15-12G / 470 15-12B.
- **Post-Form-15 continuation population (lane illustration "remaining-firm")**: 201 names have ≥1 bar strictly after the filing; continuation length median 9 bars (p25 3 / p75 29 / max 79). After inherited floors (63-bar + band ≥C + RAW ≥ $1.00): **25 events (folds 3/16/6)**; under band-only: 49 (3/23/23). Fold 1 = 3 < the frozen ≥5-per-fold minimum under BOTH readings, and 25 < the ≥30 total minimum → **INFEASIBLE, dropped at design time** (declared in both packets).
- Grid-book eligible population (structure-only): fold 1 = 315–447 (median 364), fold 2 = 173–365 (median 281), fold 3 = 0–145 (median 73; exactly one zero-eligible decision, 2025-07-14 → abstain).
- Regime paths (expanding terciles, ≥10 history; first 10 decisions abstain):
  - H1 anchor L/M/H: fold 1 9/6/2 (+10 abstain), fold 2 3/8/15, fold 3 9/5/13.
  - H2 anchor L/M/H: fold 1 5/6/6 (+10 abstain), fold 2 8/4/14, fold 3 27/0/0 (**declared asymmetry**: 15-12B events end in 2022 in the frozen FTS-enumerated census → fold-3 anchor content is entirely the 12G/long side; preregistered channel-unvalidated branch if the family passes only via fold 3).
- Band cost of the dying-cohort book: equal-weight base 16.5–19.4 bps/side across decisions (mean 18.4); stress 2×. Aggregate band counts across all 80 grid decisions: A 3,307 / B 7,723 / C 8,219 eligible; 23,245 band-D excluded at decision.
- Where the band floor cannot apply: **terminal exits** — a held name may end its series in band D; the frozen schedule has no D rate. Preregistered alternative (in both packets): band-D terminal exit fills costed at the C rate (25/50 bps) as the conservative ceiling, explicitly resolved under the L-I3 fail-closed kernel (no silent 10 bps fallback); names with <63 bars at their last session (3 in the whole dead leg) resolve at their own final band by the same rule.

## Placebo survivability (P-3 / forex V3 lesson)

Every arm — including both causal controls and the secondary placebos — is constructed so that all its inputs exist at decision time under evidenced availability semantics and it **abstains rather than aborts** when an event cannot fill (the frozen fill-check converts missing bars into "order does not exist"). Neither control can die on a data-semantics mutation: the stale-63 control counts only filings ≥63 sessions old; the label-swap control re-uses the identical filings, stamps and book machinery. No arm reads, interpolates or synthesizes any price after a series' last bar; no arm conditions on series-end in advance; no arm uses realized delisting-return magnitude as a conditioner (look-ahead — declared in both packets).

## Design-time infeasibility declarations (lane constraint honored)

1. Post-Form-15 continuation entry — infeasible under the frozen book minimums (measured counts above); the tradable residue is merger-consideration prints, not drift material.
2. OTC tails — unservable; 1,349/1,550 series end on/before the filing (median −11d); probe gate-3 evidence: dead series end at exact death sessions. Any post-series-price mechanism dropped.
3. Realized-magnitude conditioning — look-ahead by construction; magnitude enters only as the outcome of exit-at-last-close.

## Novelty vs nearest confusables (short form; full screen in each packet)

- vs **SFV3-A6-TOM-SETTLE**: no calendar/settlement cycle anywhere — the conditioner is a death-event stream that did not exist in any prior cycle (V8 cohort: 0/409 deaths).
- vs **SFV3-A5-IDIO-SHOCK-REVERSAL / momentum ancestry**: returns never ranked; no pre-death runup/reversal structure (lane boundary honored — alive-name positions are never taken or conditioned).
- vs **SFV4 participation/vol ancestry**: no dollar-volume or variance signal; ADV63 appears only as the inherited eligibility/cost floor.
- vs **SFV8-F1/F2 (V8, vetoed)**: no fundamentals field; different information set and mechanism class; measured |rho| ≤ 0.20 vs both anchors and both exposure-form shadows is a D2 gate.
- vs sibling H1 (same lane): H1 = arrival timing (stale-timing control); H2 = channel content (label-swap control); shared book machinery declared, not hidden.
- vs lanes A4/A5: no distress rank, no 154-clock fundamentals conditioning cited (price-leg branch of the dead-leg clock funding rule only).

## Self-check (recorded per lane contract)

- [x] **JSONs parse**: both packets parsed with `python3 -m json.tool` (exit 0) — see commands below.
- [x] **Fields complete**: both carry the full V8-packet section list (schema…attestation) plus the V9 lane-required sections: `event_availability_semantics`, `dead_name_book_semantics_compliance`, `infeasibility_declarations`, `margin_to_fail_expectations`, `novelty_declaration`, `outcome_blind_attestation`; `hypothesis_id` = SFV9-A6-H1 / SFV9-A6-H2; universe, clock, warmup, decision grid, fills under the frozen dead-name semantics, costs (incl. band-floor-cannot-apply + preregistered alternative), exactly three arms each, placebo runnable under evidenced semantics.
- [x] **Every event-availability statement present**: each packet's `event_availability_semantics` covers (1) filing-date availability (end-of-filed-UTC-day, conservative-later decision), (2) price availability (session close + 1), (3) the active-series filter's real-time computability, (4) expanding-regime history, (5) series-end knowability, (6) the no-post-series-prices prohibition; H2 adds (7) label authority/caveat.
- [x] **Exactly three arms per proposal** (anchor / neighbour / causal control) + a secondary placebo each, all runnable under the preregistered dead-name book semantics.
- [x] **Outcome-blind attestation** present in both packets and in this README.
- [x] **No scored computation**: nothing in this lane computed any return, PnL or metric; all cited numbers are counts/percentiles of structure (events, bars, bands, populations, regime path lengths, delta-days).
- [x] **Forbidden screen**: full `forbidden_inventory_screen` per packet incl. both V8 families, the exposure-form shadows, generic mechanisms, blocked channels, rescue-variant check.
- [x] **Single commit, explicit paths**, prefix `V9 D1 lane A6: `, no push, no `git add -A`.

Verification commands (run at packaging time):

```
python3 -m json.tool research/control/stocks_free_v9_run/proposals/a6_death_H1.json > /dev/null && echo H1_OK
python3 -m json.tool research/control/stocks_free_v9_run/proposals/a6_death_H2.json > /dev/null && echo H2_OK
git -C <worktree> rev-parse HEAD   # base 86fecae8044d344e5d5ea9a49bbcfdb2f03c0b5a before commit
```

## Known limitations (declared, not argued away)

1. H2's fold-3 content is all-long by the 12B-extinction asymmetry of the frozen census (15-12B events end in 2022) — preregistered downweighting branch if the family passes only via fold 3.
2. The form-type label is recorded EDGAR metadata, not a validated reason discriminator (the census says so itself) — the label-swap control is the preregistered arbiter.
3. Both anchors are single-sided ±1.0 books in invested decisions: the risk-matched alpha / ETF-share gates are the named most-likely binding constraints; a beta-only result must fail them.
4. Short-side legs of dying micro-caps carry borrow realism the frozen cost model does not price (commission/impact only); inherited execution semantics short such names (V8 precedent), and this limitation is recorded for D2 feasibility review in both packets.
5. The stale-63 control will earn part of the anchor's behaviour by construction (autocorrelated wave state); the family pre-commits to the frozen 0.5× control-alpha rule without argument (V4 precedent).
6. Conditioner construction shares the P0a census's own coverage boundaries (FTS enumeration; INC-V9-2 pagination incident recorded upstream) — the stream is used exactly as frozen, no re-enumeration, no gap-filling.
