# Ingestion acceptance checklist — PIT equity data authority

> Execute only AFTER the owner authorizes a provider and
> `provider_evaluation_template.json` shows every required requirement at PASS
> with referenced evidence. Until then this checklist is a plan, not a
> permission. Fail closed at every step; an unchecked box blocks scored
> research — it is never waived.

## Stage A — Pre-ingestion gates (no data touches the factory)

- [ ] Owner authorization recorded (who, when, scope, spend limit) and
      referenced in the filled evaluation template.
- [ ] License terms reviewed: research use, storage location, retention,
      redistribution. Confirmed licensed raw payloads stay OUTSIDE Git; only
      manifests/checksums tracked. (R18)
- [ ] Storage location provisioned outside the repo; append-only; access noted
      in the data manifest. (R17)
- [ ] Schema/export format documented and versioned by the provider. (R15)
- [ ] Revision/vintage policy documented in writing. (R14)

## Stage B — First delivery intake (staging only)

- [ ] Every delivered file hashed (sha256); checksum manifest created and
      committed under `research/control/stocks_run/`. (R17)
- [ ] Loader-level verification run: manifest verified before any read;
      tampered/unmanifested/missing files fail the intake. (R17)
- [ ] Row-level timestamps: exchange timestamp + ingest timestamp present,
      tz-aware, `ingest >= exchange` everywhere. (R13)
- [ ] Session reconciliation vs `US_EQUITY_REGULAR_V1` (manifest digest
      `028a7b21…`) across >= 10 years including half-days and the documented
      unscheduled closures; unexplained session conflicts = STOP, new calendar
      version required. (R13)
- [ ] NEEDS_PROVIDER_VERIFICATION list from the calendar lane (2027+ observed
      holidays) closed against the provider's official calendar.

## Stage C — PIT correctness probes (sampled, independent)

- [ ] Security master as-of replays: attributes at past decision timestamps
      match provider's own maintenance history; no current-state backfill. (R01)
- [ ] Ticker history: retired tickers do not resolve late, new ones not early;
      identifier continuity check on a ticker-change sample. (R03)
- [ ] Delistings: census vs independent death records; bars retained through
      final valid event; delist reasons present. (R04, R07)
- [ ] Index membership (F1): every add/delete carries distinct announcement vs
      effective timestamps, both with ingest stamps; sample audit vs public
      announcements. (R02, R06)
- [ ] Corporate actions: splits/dividends applied at ex/effective dates;
      declared (announcement) timestamps distinct; golden spot-checks vs
      exchange records. (R05)
- [ ] Prices: raw -> adjusted -> raw round-trip with frozen factors; fill path
      stays raw; total-return path declared. (R08)
- [ ] Executable price/volume: fields carry executable semantics per venue
      documentation; volume units unambiguous. (R09)
- [ ] Benchmark: SPY total return + price + dividends delivered, checksummed,
      restatement policy noted. (R10)
- [ ] Borrow (F2): availability, fee/rate with declared accrual basis (360),
      utilization — all effective-dated daily; recall policy documented; a
      sampled locate log reconciles. (R11, R12)
- [ ] Gap census computed by the as-built loader/audit reconciles with the
      provider's missing-data and correction policy. (R19)

## Stage D — Floor validation on loader-resolved values

- [ ] >= 8 years daily history across the common eligible population. (R16)
- [ ] >= 30 eligible liquid names per cross-sectional decision. (R16)
- [ ] Intraday >= 3 years IF any arm's scored execution clock requires it. (R16)
- [ ] Floors computed from loader-resolved values, never from file presence.

## Stage E — Freeze and handoff

- [ ] `data_manifest.json` written: provider identity, schema digest, vintage,
      checksums, coverage census, calendar reconciliation report, license
      reference, policy notes.
- [ ] S0 end frozen at least 12 months before the latest complete provider
      date; the following non-overlapping period SEALED as S1 (never opened
      this sprint). (PLAN_stocks §7)
- [ ] SD0_DATA_PIT_PASS re-run on real data; gate evidence recorded with the
      new manifest digests.
- [ ] Window/fold/purge policy frozen per PLAN_stocks §10; only then may
      S4/S5/S6 dispatch under the standing budget 0/6.
- [ ] Any drift discovered later (restatement, calendar conflict) invalidates
      the affected manifest and creates a NEW data identity — no silent patch.

## Failure handling

Any failed or unchecked item above: record `FAIL`/`NOT_RUN` with evidence in
`research/control/stocks_run/gates/`, keep
`data_authority_verdict = UNAVAILABLE_FAIL_CLOSED`, and do not proceed to S4.
