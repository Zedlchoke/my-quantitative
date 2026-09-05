# AMBIGUITIES — FXFV4-A6-P2 implementation (lane I-FAMILY-2) — for A1

Recorded per the lane contract: ambiguities that could not be resolved from
the frozen packet + binding directives are WRITTEN DOWN here, never resolved
by judgment that affects scores (no scores were computed in this lane).

## A-1 (material): RESOLVED_BY_A1 — the frozen mapping table governs

`PROPOSAL_FXFV4-A6-P2.json`, `arms.control.sham_derangement_frozen`:

- rule text: `sham(X) = area_order[(index(X)+3) mod 8]` — a +3 rotation,
  which yields US->JP (drives USD/JPY).
- explicit mapping table (verbatim): `US -> drives USD/CHF`, `EMU -> USD/CAD`,
  `GB -> AUD/USD`, `JP -> NZD/USD`, `CH -> drives all 7`, `CA -> EUR/USD`,
  `AU -> GBP/USD`, `NZ -> USD/JPY` — a +4 rotation.

RESOLUTION IMPLEMENTED: the mapping TABLE (`SHAM_AREA` in family2.py).
**A1 ADJUDICATION (binding, research/control/forex_free_v4_run/
a1_ambiguity_adjudication.json): the lane's choice STANDS — the frozen
mapping table governs; no change.** A1 may still wish to reconcile the
packet's `+3` rule sentence at the next frozen revision.

## A-2 (material): RESOLVED_BY_A1 — eligibility = `first_readable_decision_utc`

The original lane implementation keyed eligibility to the row's operative
availability stamp alone (packet mechanism text `T >= a`); the ledger's
`first_readable_decision_utc` field equals `first 16:00-NY bar >=
max(operative availability, effective)` on all 151 deduped RATE_CHANGE
rows, and the two rules differ exactly on the 87 evidenced rows whose
availability stamp precedes their effective instant (US/AU INSTANT
announcements the day before effectiveness; NZ/CH/JP DAY rows).

**A1 ADJUDICATION (binding, research/control/forex_free_v4_run/
a1_ambiguity_adjudication.json): OVERRIDES the availability-only
implementation. Eligibility for every RATE_CHANGE row is the row's
PRECOMPUTED `first_readable_decision_utc` (fail closed when null,
MISSING_AVAILABLE_TIME_EVIDENCE class) — the frozen program PIT invariant:
a decision never reads a row whose effective_time_utc > T. Availability-
only eligibility would read a rate before it is in force. Financing
vintages keep BOTH gates (unchanged).**

APPLIED in family2.py (remediation commit): `extract_events` anchors
`eligible_dt` on `first_readable_decision_utc` (null -> never read);
`run_arm`/`schedule_counts` schedule from `eligible_dt` (+180d bench shift
on that instant); the deterministic tie-break still uses the operative
availability instant, falling back to the eligibility instant. Synthetic
tests updated: the discriminator now pins a row whose precomputed
first_readable sits later than any locally derivable instant, and the
87-row class (pre-effective announcement) is asserted to become eligible
only at/after the effective instant.

DISCLOSED LEDGER FACT (found during remediation, pinned-row smoke test):
exactly ONE pinned row (CA eff 2020-03-27, COVID era) carries a
SATURDAY-stamped `first_readable_decision_utc` (2020-03-28T20:00Z = Sat
16:00 NY). The frozen rule handles it fail-safe: no completed 16:00-NY
flat bar exists that day, so the decision lands on the first EXISTING
weekday decision bar at/after the stamp (Mon 2020-03-30). No row is read
before its stamp; recorded here so the Monday decision on that one event
surprises no one at scoring time.

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
