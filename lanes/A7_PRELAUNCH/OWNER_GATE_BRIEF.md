# OWNER GATE BRIEF — WNBA-PLAYERFEAT-SCORED-V1 (A7 independent prelaunch audit, 2026-10-05)
A7 VERDICT: **A7_PRELAUNCH_PASS** — 9/9 checks, 0 blockers (full record: lanes/A7_PRELAUNCH/).
THE ONE GO DECISION: run the 2-arm walk-forward OOS evaluation — B0 (0.603755 train floor,
per-fold refit per packet law) vs B1-WNBA (K=32/HCA=50/γ=0.65, warm-up 1997–2001) — on the
frozen window [2020..2026], completed seasons only, single batch, one computation per arm,
under the heavy lock, after the owner types GO verbatim at this cycle's own gate.
Metrics/falsifiers already frozen: LL primary; Brier/reliability/slope band [0.85,1.15];
paired tip-date-cluster bootstrap 10,000 resamples seed 20261005; B1 REJECT vs B0 iff the
pooled 95% CI of ΔLL includes 0 OR ≥ half of season folds are non-negative.
OWED BEFORE ANY CONTINUITY RE-PROPOSAL: WF-A machinery audit (time-shuffled twin beat its OWN
parent by ΔLL −0.000968; parent real-data fold slope 0.9047 inside [0.85,1.15] so no exemption
applied; arm UN-SCORED this cycle).
STAYS FORBIDDEN: typing/consuming GO anywhere but this cycle's own gate; any OOS read before
GO; second-look/re-batching of OOS after the single batch; NBA parameters as WNBA evidence;
S1 access, betting/live/purchase vocabulary, push, merge to main, history rewrite, writes to
 registries/ledgers outside the cycle's own gates; WF-B/WF-C stay RELEASED (φ=0, no signal);
feature k-selection (k=3 variant) stays deferred, never scored retroactively.
Frozen inputs the post-GO read must consume verbatim: feature table sha ceaf10ba…,
harness b9446f76… / arms 82263eab…, ledger 603aa412…, summary bf62d37a…, stream 6a5404be….
