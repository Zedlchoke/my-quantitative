# P7 REPRODUCTION RECEIPTS — PHASE-STRATEGY-V1 (G8)

measured_at: 2026-09-23T11:0x+07 (successor Lead session, closeout)
method: `shasum -a 256` over the five committed scored artifacts, compared
across the three independent computation trees. No file was modified; all
three source trees verified clean (`git status --porcelain` empty on
integration@a9c8a67c-parent evidence and a7-terminal@af52f358; repro-twin
differs from its base ONLY by the untracked runtime output recorded here).

| artifact                       | primary (integration 17a1bea5) | twin (detached a9c8a67c00c785c00c910c34117e50e72c62deee) | A7 recompute (a7-terminal af52f358) |
|--------------------------------|--------------------------------|----------------------------------------------------------|-------------------------------------|
| scored_ledger.json             | e59124a370293df6…              | e59124a370293df6…                                        | e59124a370293df6…                   |
| ingest_verification.json       | 2e2079a2c4cd80a1…              | 2e2079a2c4cd80a1…                                        | 2e2079a2c4cd80a1…                   |
| tiers/tier_1.0x.json           | e889fb70d8e673e8…              | e889fb70d8e673e8…                                        | e889fb70d8e673e8…                   |
| tiers/tier_1.5x.json           | 014943164b4f42c0…              | 014943164b4f42c0…                                        | 014943164b4f42c0…                   |
| tiers/tier_2.0x.json           | 43800cc4b81d252a…              | 43800cc4b81d252a…                                        | 43800cc4b81d252a…                   |

Verdict: **BYTE_MATCH 5/5 across three independent runs** — G8 discharged
three times over: (1) primary scored run (committed 17a1bea5, produced by
code state a9c8a67c under the machine-wide heavy lock, ingest 284/284 PASS);
(2) detached twin worktree `.worktrees/phase-strategy-v1/repro-twin` at
a9c8a67c00c785c00c910c34117e50e72c62deee, run recorded in its untracked
runtime/scored (file mtimes 17:23–17:24 +0700, same day); byte-copies of the
twin run's scored_ledger.json + ingest_verification.json preserved in
`repro_twin_artifacts/` here (byte-equal to the committed primary by the
table above); (3) A7 terminal fresh-context in-situ recompute, documented in
`audits/a7_terminal_audit.json` C3 (worktree a7-terminal, head af52f358).

Lock state at receipt measurement: machine-wide heavy lock FREE_PROVEN
(`researchctl locks inspect`, no worker registered). The primary run's lock
discipline is in the heavy-lock history (role A1-SCORED-RUN, FINISHED); the
A7 recompute ran WITHOUT the lock wrapper after a FREE inspection — deviation
disclosed by the auditor in its own audit C3, single worker at run time.

Incident note (handover): the PSV1 Lead session that produced the scored run
went quiet after committing scored evidence (10:21Z) with the registry row
still at pre-run state; the twin and A7-terminal artifacts it left behind are
adopted here as valid evidence after independent re-verification (this
receipt). Registry staleness is cured by the half-2 close commit.
