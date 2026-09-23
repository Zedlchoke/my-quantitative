# INC-2 — B_basis truncated by short-page break (2026-09-24 ~01:00Z)

Symptom: phase-B basis files for several symbols held a few hundred rows
(DOGE 298, BOME 428, ENA 486) instead of tens of thousands of buckets.

Diagnosis (direct probes): /futures/data/basis serves FULL depth (BTCUSDT
2021/2022/2023/2024 windows return complete 97/97 daily buckets; DOGE
2021-06 complete). Truncation was the CHR3F phase-B runner:
`if len(batch) < 500: break` treated a short page (mid-history GAP) as
end-of-data. The frozen script is NOT affected (advances unconditionally;
zero-gap check — A_basis 70,272/symbol PASS).

Fix: advance to last-served+1 bucket on short pages; empty pages advance by
page span with a 40-page guard; 33 truncated artifacts quarantined to
staging/inc2_quarantine/; 19 symbols restage with fixed code (~16h paced).

Fallout: XSECT + ILLIQ data UNAFFECTED (klines+funding complete, 40/40
verified pre-INC-2). XSECT fold census PASS — all folds incl. Y2020P have
0 stamps missing any symbol's 7d funding; fold-4 = Y2020P. Only BASISLV
B_basis restages; its readiness shifts by the restage duration.
