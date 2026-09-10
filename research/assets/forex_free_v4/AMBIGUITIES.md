# FXFV4-A6-P1 family1 — recorded ambiguities (for A1)

Lane I-FAMILY-1 implemented the frozen packet mechanically. The items below
are points where the packet text admits more than one mechanical reading, or
where the task/directive text and the packet text differ in emphasis. Items
marked RESOLVED were pinned to a single frozen convention in code (with the
authority used); none was resolved by outcome-affecting judgment beyond what
the frozen spec + directives force. Items marked OPEN need an A1 ruling
before any scored run; each is isolated behind a single named constant or a
scoring-time surface so a ruling cannot require re-implementing the module.

1. RESOLVED (no score effect) — `decision_ts` label: bar stamp vs completion
   instant. The packet mechanism says the decision happens "at the completion
   instant of each daily 16:00 America/New_York flat bar" while its own
   `pit_observable` says the bar "stamps 20:00Z in EDT weeks / 21:00Z in EST
   weeks", and the frozen V3 validator (`_is_ny_1600`) refuses any decision
   instant not at 16:00 NY wall time. Pinned: `decision_ts` = the 16:00-NY
   bar instant (the validator-compatible stamp, matching the packet's
   parenthetical); the trigger is computed at that bar's completion from
   completed closes, strictly before the next-session fill. Both readings
   produce byte-identical fills, prices, holds and PnL — only the
   decision-instant label differs by one hour.

2. RESOLVED (conservative, provider-grid-free) — "a NY-day is valid only if
   all of that day's completed H1 bars exist" needs a per-day expected
   bar-count convention (the a9 audit's recorded ambiguity). The frozen
   inputs do not state the provider's hourly grid (the real snapshot's
   ~42.7k bars/pair over 6.6y does not match a cleanly derivable weekly
   count), and hard-coding a guessed grid could falsely invalidate every
   real day. Pinned definition (`ny_day_valid_map`): a NY-day is valid for a
   pair iff that day's 16:00-NY completed bar exists AND the pair's bars of
   that NY-day are gap-free (consecutive 1-hour steps). This fails closed on
   interior holes, full holidays (no 16:00 bar) and early closes (session
   ends before 16:00), and never fails on healthy data regardless of the
   provider's exact open/close hours. If A1 prefers a strict expected-count
   table, it slots into `ny_day_valid_map` alone.

3. OPEN (affects trigger values on real data; one-constant switch) — the z
   denominator's standard deviation convention. The packet says
   `std(same 60 days)` without stating sample (ddof=1) vs population
   (ddof=0). Pinned: SAMPLE standard deviation, `statistics.stdev`, frozen
   constant `Z_STD_DDOF = 1` (the pandas/statistics convention; the two
   differ by a factor sqrt(60/59) ≈ 1.0084, enough to move borderline
   z <= −1.0 firings). A1 can flip the constant; the hand goldens pin the
   current choice explicitly.

4. OPEN (scoring-time harness mapping; audit A6P1-M2) — the packet's 6-scenario
   drop-one suite (5 leg-drops + best-fold drop, 5-of-6 survival) vs the
   frozen kernel's DROPOUT_SCENARIOS=8 / DROPOUT_MIN_SURVIVAL=6 harness. The
   5 leg-drop schedules are exposed family-side (`drop_one_leg_schedule`,
   non-vacuity tested); the best-fold drop is the runner's inherited
   dropout scenario; the survival-gate arithmetic over the 6-scenario
   denominator is a scoring-time surface this lane cannot own without
   modifying the V3 runner. A1/A7 must pin: parameterize the harness to 6
   scenarios, or evaluate the 5 leg-drops inside the 8-scenario suite plus
   the inherited fold-drop (the audit ruled either mechanical).

5. RESOLVED (packet text decisive) — "exit at the open of the 16:00-NY bar
   after the 5th completed NY-day (following entry)". Pinned: exit bar =
   the 5th existing daily bar AFTER the entry bar in the leg's own 16:00-NY
   bar sequence, i.e. exactly 5 completed daily closes occur during the hold
   (the packet's "holds exactly 5 completed NY-days" is the binding phrase).
   The alternative reading (exit at +6 sessions) would hold through 6
   completed closes and contradicts it.

6. RESOLVED (mechanical, fail-closed) — daily log returns run over
   consecutive VALID trigger days: when an invalid day is skipped, the next
   valid day's return spans the gap (e.g. over a holiday) rather than being
   voided; the skipped day contributes no close and is never backfilled.
   Symmetrically, entry/exit FILL bars need only exist (bar-existence is the
   packet's fill criterion, "missing entry/exit bar => signal voided");
   trigger-day validity is a trigger-pair concept only.

7. RESOLVED (mechanical) — fold-boundary interaction. An entry whose fill
   would land exactly on the boundary force-flat bar is suppressed
   (NO_TRADE — it would be force-flattened into a zero-length round trip).
   An entry decided ON the force-flat bar fills at the first bar AFTER the
   boundary and is scored in the next fold by the runner's `fold_of`
   (entry-instant) semantics; the packet's "no position crosses a fold
   boundary" is satisfied because the position [entry..exit] lies entirely
   after the boundary. The span-end boundary (2026-09-02) force-flats at the
   last existing bar so no position survives past the final bar.

8. NOTE (task text vs packet text) — the mandated "no-lookahead mutation
   test that FAILS if the trigger reads the decision bar": the frozen
   mechanism's S_t necessarily reads day t's completed close (that IS the
   signal), while the packet freezes the STANDARDIZATION WINDOW to the 60
   days strictly before t. The implemented mutation test pins exactly that:
   a mutated z whose window includes the decision day differs from the hand
   golden, and perturbing every close strictly after the decision day leaves
   the schedule identical. "Reads the decision bar" is therefore enforced as
   "reads the decision bar in its own standardization window (or any later
   bar)", which is the only reading consistent with the frozen law.

9. NOTE (no action) — the a9 audit's LOW finding A6P1-L2 (citation
   misattribution: the price span 2020-01-30..2026-09-02 is recorded in the
   w1_freeze loader manifest, not p2_data_authority_v4.json) is cosmetic;
   no code depends on it. The span itself is enforced nowhere in the module
   (the fold grid and fail-closed loaders govern); scored-window clipping
   remains runner-side (`fold_of` warmup region) as inherited.
