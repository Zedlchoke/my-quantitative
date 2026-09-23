# JRV2 — REGIME CLASSIFICATION REPORT (frozen corpus, classification-only)

Model pin `jev-1.13.0` (VERIFIED_LIVE, zero drift across 13,315 calls). Prompt
V1_amendment_2 (trial-1) frozen before the first historical call. Forced-choice
4-phase; abstention code-owned. Full per-cell manifests: `bulk_response_manifest_<cell>.json`.

## Corpus

| Cell | Decisions | Provider OK | Fail-closed errors | Usage (in/out) |
|---|---|---|---|---|
| BTC_H1 | 8,567/8,567 | 8,550 | 17 (6 schema, 8 timeout, 3 provider) | 37.5M / 1.10M |
| BTC_H4 | 1,997/1,997 | 1,994 | 3 | 8.7M / 0.26M |
| SPY_D1 | 2,751/2,751 | 2,750 | 1 | 11.6M / 0.36M |
| **Total** | **13,315/13,315** | 13,314 | 21 (0.16%) | **58.05M / 1.745M** (used-only; A7-2 convention) |

## Effective/persisted regime occupancy

| Cell | effUNKNOWN | Persisted occupancy (ACC/UP/DIST/DOWN/UNKNOWN) | Switches | Max UNKNOWN run |
|---|---|---|---|---|
| BTC_H1 | 42.7% | .34 / .21 / .19 / .26 / .00 | 90 | 6 bars |
| BTC_H4 | 27.2% | .10 / .31 / .14 / .45 / .00 | 31 | 7 bars |
| SPY_D1 | 29.1% | .00 / .70 / .03 / .26 / .01 | 34 | 14 bars |

No UNKNOWN_COLLAPSE (contrast V1: 100% persisted UNKNOWN). All four phases are
used on every asset; persistence dwell is healthy (median switch cadence
~95/69/81 regime bars; never stuck).

## Confidence & stability

Canary (trial-1): phase correct 4/4 clear fixtures; directional fixtures 2/2
not inverted; perturbation stability 8/8 per clear family; raw phase balance
1/1/1/1 across clear fixtures. One preregistered criterion failed
(ambiguous-fixture code-abstention: the model answers confidently on
mixed evidence; forced-choice removes its uncertainty channel — C5/C7) and
provider NONDETERMINISM was observed (C7 same bytes -> RANGE vs TREND across
trials). Historical preview (100 timestamp-sampled states): no collapse
(UNKNOWN 0.44). Repeated-decision stability beyond canaries: not re-measured
in bulk (each state called exactly once by law).

## Answering the owner's five-year-old questions (classification half)

Jev đọc được thời tiết (đủ 4 loại, đúng hướng trên fixture rõ, không sụp).
Nó đổi ý vừa phải (31–90 lần/năm-cell, không run rẩy). Câu hỏi còn lại —
chọn theo nó có lợi không — do REGIME_BACKTEST_REPORT trả lời.
