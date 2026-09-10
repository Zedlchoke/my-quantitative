# AMBIGUITIES — FXFV4-A6-P2 implementation (lane I-FAMILY-2) — for A1

Recorded per the lane contract: ambiguities that could not be resolved from
the frozen packet + binding directives are WRITTEN DOWN here, never resolved
by judgment that affects scores (no scores were computed in this lane).

## A-1 (material): the packet's control rule text contradicts its own mapping table

`PROPOSAL_FXFV4-A6-P2.json`, `arms.control.sham_derangement_frozen`:

- rule text: `sham(X) = area_order[(index(X)+3) mod 8]` — a +3 rotation,
  which yields US->JP (drives USD/JPY).
- explicit mapping table (verbatim): `US -> drives USD/CHF`, `EMU -> USD/CAD`,
  `GB -> AUD/USD`, `JP -> NZD/USD`, `CH -> drives all 7`, `CA -> EUR/USD`,
  `AU -> GBP/USD`, `NZ -> USD/JPY` — a +4 rotation.

RESOLUTION IMPLEMENTED: the mapping TABLE (`SHAM_AREA` in family2.py).
Basis: the lane directive cites "the packet's exact mapping"; the A9-F
control_runnability note for this family also uses the table ("US 22x7 ->
USD/CHF only; CH 11 -> all 7"). Both derivations are derangements, so the
control's role (destroy the area-specific link) holds under either; A1 may
wish to reconcile the packet text at the next frozen revision.

## A-2 (material): decision instant vs the ledger's `first_readable_decision_utc`

The frozen mechanism text (packet `mechanism`, `pit_observable.decision_clock`,
`source_to_test_map` — three places) and the lane task define eligibility as
`T = first completed 16:00-NY bar with completion >= operative_available_time_utc`,
keyed to the OPERATIVE AVAILABILITY STAMP ALONE. The ledger additionally
carries `first_readable_decision_utc`, which equals `first 16:00-NY bar >=
max(operative_available_time_utc, effective_time_utc)` on ALL 151 deduped
RATE_CHANGE rows (verified by recomputation) — i.e. it embeds the V3R
evidenced-vintages reader invariant (`available <= T AND effective <= T`,
cf. `research/control/forex_free_v4_run/build_evidenced_vintages.py`
docstring). The two rules differ ONLY on the 87 evidenced rows whose
availability stamp precedes their effective instant (US/AU INSTANT
announcements the day before effectiveness; NZ/CH/JP DAY rows), where the
implemented (availability-only) decision lands one session EARLIER than the
`first_readable_decision_utc` value.

RESOLUTION IMPLEMENTED: availability-only, per the frozen mechanism text and
the lane directive ("at/after the row's operative availability stamp; never
on the effective date itself"). The FINANCING reads, in contrast, keep BOTH
gates (availability AND effectiveness) exactly as the packet's frozen
financing formula text specifies, so financing never accrues a rate before it
is in force. If A1 intends the decision clock to honor
`first_readable_decision_utc` (max-gate), that is a one-line change in
`run_arm`'s eligibility anchor but it CHANGES THE SCORED SCHEDULE — decide
before any scored run.

## A-3 (minor): exit-bar reading of "the 16:00-NY bar after the H-th completed NY-day following entry"

Implemented as: the exit bar is the H-th EXISTING 16:00-NY bar after the
entry bar (open fill), i.e. the entry day itself is the 1st NY-day that
completes after the entry instant, and exactly H NY-days complete between
the entry open and the exit open. The alternative reading (bar H+1) would
hold H+1 sessions. Chosen reading matches "hold 10 completed NY-days"
literally (10 days elapse while held) and keeps the H=1 degenerate case a
strict one-session round trip. Hand-computed goldens pin it.

## A-4 (minor, disclosed in-packet): the +180d benchmark's tail asymmetry

Events late in the window (roughly the last 6 months) have no stale twin:
their +180d availability falls past the snapshot. Implemented behavior:
`NO_DECISION_BAR_AVAILABLE` skip (counted in meta), never backfilled. This
is the A6P2-L2-accepted consequence of the frozen constant.

## A-5 (minor): purge-window "either side" bookkeeping

The kernel's `fold_of` (mirrored) purges ENTRIES within 14 calendar days
AFTER a fold start and excludes the warmup region. The packet adds "trades
whose entry OR exit instant falls inside a purge window are excluded from
fold statistics and counted in purge_excluded"; the exit side is implemented
in `assemble_cell_record` as `purge_excluded_exit_side` (exit within
`[boundary - 14d, boundary)`, internal boundaries), and such trades are
excluded from the scored book like kernel-purged trades. The V4 runner lane
should confirm this book composition (kernel-only semantics would keep
exit-side-purged trades in the book).

## A-6 (cosmetic): packet prose counts on the raw 212-row basis

Already recorded by the binding directive ("A6-P2 drops the packet's
raw-count turnover basis; canonical deduped counts govern"). Implemented on
the deduped 151-event basis throughout (`meta.events` carries raw=220,
deduped=159, rate_change=151, events_used=151 for the pinned ledger).

## A-7 (cosmetic): packet's "~1.8-day median effective->readable lag" sentence

That statistic reproduces only on the RAW row basis and describes the
ledger's `first_readable_decision_utc` column (see A-2); on the deduped
basis with the implemented availability-only decision clock the effective->
decision lag differs per row group. Recorded so the sentence is not read as
an implementable rule; it does not gate anything.
