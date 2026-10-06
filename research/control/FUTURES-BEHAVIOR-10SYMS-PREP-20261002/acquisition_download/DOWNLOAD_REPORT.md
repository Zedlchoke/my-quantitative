# DOWNLOAD_REPORT — Databento chunked download (lane ACQ-DOWNLOAD)

Task FUTURES-BEHAVIOR-10SYMS-PREP-20261002 · generated 2026-10-02T22:40:14+00:00

- Authority: owner approval 2026-10-02 (ceiling $125 from credit; chunked download; iCloud mirror) + owner RESCOPE 2026-10-02 (verbatim: 'tôi muốn NQ ES 6E 6J 6B 6A thôi. Tải trong 125 đô đó. Còn lại mắc quá tính sau.'). Lane hard stop $118 (quote-vs-bill drift buffer).
- Package evolution: A-v1 $129.57 → A-v1-trim C3_staggered_9m_6m $113.05 → RESCOPE $105.81 (dropped GC/SI/CL/NG ohlcv, avoided $81.65, zero spent on them; added NQ/ES 2010-06-06→2023-10-01 deltas + FX 2022 backfills; definitions/statistics ALL10 kept).
- Batch API: official client v0.87.0 (batch.submit_job, dbn+zstd, split_duration=none, delivery=download, stype parent->instrument_id). get_cost docstring states it prices 'historical streaming or batched files' — same per-GB path; per-chunk quotes re-taken before every submit (budget law); vendor sha256 hashes verified on every file.

## Per-batch table

| # | chunk | schema | window | records (quoted→actual, drift) | raw .dbn.zst | parquet | get_cost | committed after | QA | state |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `AV1T-definition-ALL10__2023-10-01_2024-01-01` | definition | 2023-10-01..2024-01-01 | 928,106→928,106, 0.0% | 16,342,168 B | 3,682,664 B | $0.7641 | $0.7641 | PASS | MIRRORED |
| 2 | `AV1T-definition-ALL10__2024-01-01_2024-04-01` | definition | 2024-01-01..2024-04-01 | 956,349→956,349, 0.0% | 16,907,069 B | 4,018,081 B | $0.7874 | $1.5515 | PASS | MIRRORED |
| 3 | `AV1T-definition-ALL10__2024-04-01_2024-07-01` | definition | 2024-04-01..2024-07-01 | 971,798→971,798, 0.0% | 16,936,580 B | 4,101,056 B | $0.8001 | $2.3515 | PASS | MIRRORED |
| 4 | `AV1T-definition-ALL10__2024-07-01_2024-10-01` | definition | 2024-07-01..2024-10-01 | 1,001,619→1,001,619, 0.0% | 17,681,530 B | 4,325,616 B | $0.8246 | $3.1761 | PASS | MIRRORED |
| 5 | `AV1T-definition-ALL10__2024-10-01_2025-01-01` | definition | 2024-10-01..2025-01-01 | 973,164→973,164, 0.0% | 17,270,153 B | 4,189,090 B | $0.8012 | $3.9773 | PASS | MIRRORED |
| 6 | `AV1T-definition-ALL10__2025-01-01_2025-04-01` | definition | 2025-01-01..2025-04-01 | 988,583→988,583, 0.0% | 17,656,348 B | 4,399,549 B | $0.8139 | $4.7912 | PASS | MIRRORED |
| 7 | `AV1T-definition-ALL10__2025-04-01_2025-07-01` | definition | 2025-04-01..2025-07-01 | 1,051,276→1,051,276, 0.0% | 18,651,066 B | 4,800,964 B | $0.8655 | $5.6567 | PASS | MIRRORED |
| 8 | `AV1T-definition-ALL10__2025-07-01_2025-10-01` | definition | 2025-07-01..2025-10-01 | 1,053,798→1,053,798, 0.0% | 18,662,978 B | 4,806,334 B | $0.8676 | $6.5243 | PASS | MIRRORED |
| 9 | `AV1T-definition-ALL10__2025-10-01_2026-01-01` | definition | 2025-10-01..2026-01-01 | 1,087,623→1,087,623, 0.0% | 19,629,882 B | 5,038,773 B | $0.8954 | $7.4197 | PASS | MIRRORED |
| 10 | `AV1T-definition-ALL10__2026-01-01_2026-04-01` | definition | 2026-01-01..2026-04-01 | 1,021,949→1,021,949, 0.0% | 18,874,775 B | 4,659,046 B | $0.8414 | $8.2611 | PASS | MIRRORED |
| 11 | `AV1T-definition-ALL10__2026-04-01_2026-07-01` | definition | 2026-04-01..2026-07-01 | 1,061,044→1,061,044, 0.0% | 19,646,521 B | 4,919,073 B | $0.8735 | $9.1346 | PASS | MIRRORED |
| 12 | `AV1T-definition-ALL10__2026-07-01_2026-10-01` | definition | 2026-07-01..2026-10-01 | 1,061,732→1,061,732, 0.0% | 19,289,158 B | 5,227,919 B | $0.8741 | $10.0088 | PASS | MIRRORED |
| 13 | `AV1T-statistics-ALL10__2023-10-01_2023-12-01` | statistics | 2023-10-01..2023-12-01 | 3,426,410→3,426,410, 0.0% | 59,050,460 B | 29,563,610 B | $0.2553 | $10.2640 | PASS | MIRRORED |
| 14 | `AV1T-statistics-ALL10__2023-12-01_2024-02-01` | statistics | 2023-12-01..2024-02-01 | 3,252,634→3,252,634, 0.0% | 55,199,099 B | 26,857,847 B | $0.2423 | $10.5064 | PASS | MIRRORED |
| 15 | `AV1T-statistics-ALL10__2024-02-01_2024-04-01` | statistics | 2024-02-01..2024-04-01 | 3,031,084→3,031,084, 0.0% | 49,923,077 B | 24,856,863 B | $0.2258 | $10.7322 | PASS | MIRRORED |
| 16 | `AV1T-statistics-ALL10__2024-04-01_2024-06-01` | statistics | 2024-04-01..2024-06-01 | 3,315,478→3,315,478, 0.0% | 55,559,942 B | 27,346,014 B | $0.2470 | $10.9792 | PASS | MIRRORED |
| 17 | `AV1T-statistics-ALL10__2024-06-01_2024-08-01` | statistics | 2024-06-01..2024-08-01 | 3,207,260→3,207,260, 0.0% | 53,750,772 B | 26,880,210 B | $0.2390 | $11.2182 | PASS | MIRRORED |
| 18 | `AV1T-statistics-ALL10__2024-08-01_2024-10-01` | statistics | 2024-08-01..2024-10-01 | 3,366,140→3,366,140, 0.0% | 56,755,111 B | 28,182,001 B | $0.2508 | $11.4690 | PASS | MIRRORED |
| 19 | `AV1T-statistics-ALL10__2024-10-01_2024-12-01` | statistics | 2024-10-01..2024-12-01 | 3,334,717→3,334,717, 0.0% | 56,370,559 B | 27,890,814 B | $0.2485 | $11.7175 | PASS | MIRRORED |
| 20 | `AV1T-statistics-ALL10__2024-12-01_2025-02-01` | statistics | 2024-12-01..2025-02-01 | 3,466,270→3,466,270, 0.0% | 59,538,301 B | 29,554,065 B | $0.2583 | $11.9757 | PASS | MIRRORED |
| 21 | `AV1T-statistics-ALL10__2025-02-01_2025-04-01` | statistics | 2025-02-01..2025-04-01 | 3,572,589→3,572,589, 0.0% | 60,643,206 B | 29,962,993 B | $0.2662 | $12.2419 | PASS | MIRRORED |
| 22 | `AV1T-statistics-ALL10__2025-04-01_2025-06-01` | statistics | 2025-04-01..2025-06-01 | 4,186,035→4,186,035, 0.0% | 74,006,175 B | 35,296,797 B | $0.3119 | $12.5538 | PASS | MIRRORED |
| 23 | `AV1T-statistics-ALL10__2025-06-01_2025-08-01` | statistics | 2025-06-01..2025-08-01 | 3,993,452→3,993,452, 0.0% | 68,871,283 B | 33,479,824 B | $0.2975 | $12.8513 | PASS | MIRRORED |
| 24 | `AV1T-statistics-ALL10__2025-08-01_2025-10-01` | statistics | 2025-08-01..2025-10-01 | 3,702,839→3,702,839, 0.0% | 62,355,752 B | 30,700,353 B | $0.2759 | $13.1272 | PASS | MIRRORED |
| 25 | `AV1T-statistics-ALL10__2025-10-01_2025-12-01` | statistics | 2025-10-01..2025-12-01 | 4,027,563→4,027,563, 0.0% | 70,544,006 B | 33,906,243 B | $0.3001 | $13.4273 | PASS | MIRRORED |
| 26 | `AV1T-statistics-ALL10__2025-12-01_2026-02-01` | statistics | 2025-12-01..2026-02-01 | 4,423,902→4,423,907, 0.0001% | 79,607,950 B | 37,851,692 B | $0.3296 | $13.7569 | PASS | MIRRORED |
| 27 | `AV1T-statistics-ALL10__2026-02-01_2026-04-01` | statistics | 2026-02-01..2026-04-01 | 5,233,786→5,233,786, 0.0% | 99,155,329 B | 45,145,060 B | $0.3899 | $14.1468 | PASS | MIRRORED |
| 28 | `AV1T-statistics-ALL10__2026-04-01_2026-06-01` | statistics | 2026-04-01..2026-06-01 | 4,651,189→4,651,189, 0.0% | 86,019,828 B | 40,426,036 B | $0.3465 | $14.4934 | PASS | MIRRORED |
| 29 | `AV1T-statistics-ALL10__2026-06-01_2026-08-01` | statistics | 2026-06-01..2026-08-01 | 4,559,590→4,559,590, 0.0% | 82,718,093 B | 38,841,856 B | $0.3397 | $14.8331 | PASS | MIRRORED |
| 30 | `AV1T-statistics-ALL10__2026-08-01_2026-10-01` | statistics | 2026-08-01..2026-10-01 | 4,314,098→4,314,098, 0.0% | 78,489,352 B | 37,248,126 B | $0.3214 | $15.1545 | PASS | MIRRORED |
| 31 | `AV1T-O1M-ES__2023-10-01_2024-04-01` | ohlcv-1m | 2023-10-01..2024-04-01 | 278,464→278,464, 0.0% | 3,676,744 B | 3,819,667 B | $1.0166 | $16.1711 | PASS | MIRRORED |
| 32 | `AV1T-O1M-ES__2024-04-01_2024-10-01` | ohlcv-1m | 2024-04-01..2024-10-01 | 286,409→286,409, 0.0% | 3,884,988 B | 3,862,967 B | $1.0456 | $17.2167 | PASS | MIRRORED |
| 33 | `AV1T-O1M-ES__2024-10-01_2025-04-01` | ohlcv-1m | 2024-10-01..2025-04-01 | 290,016→290,016, 0.0% | 4,002,109 B | 3,791,147 B | $1.0588 | $18.2755 | PASS | MIRRORED |
| 34 | `AV1T-O1M-ES__2025-04-01_2025-10-01` | ohlcv-1m | 2025-04-01..2025-10-01 | 282,747→282,747, 0.0% | 3,944,593 B | 4,036,781 B | $1.0322 | $19.3078 | PASS | MIRRORED |
| 35 | `AV1T-O1M-ES__2025-10-01_2026-04-01` | ohlcv-1m | 2025-10-01..2026-04-01 | 280,521→280,521, 0.0% | 4,006,438 B | 3,673,870 B | $1.0241 | $20.3319 | PASS | MIRRORED |
| 36 | `AV1T-O1M-ES__2026-04-01_2026-10-01` | ohlcv-1m | 2026-04-01..2026-10-01 | 279,511→279,511, 0.0% | 4,013,050 B | 3,937,074 B | $1.0204 | $21.3523 | PASS | MIRRORED |
| 37 | `AV1T-O1M-GC__2023-10-01_2024-04-01` | ohlcv-1m | 2023-10-01..2024-04-01 | — | 0 B | 0 B | $0.0000 | $21.3523 | — | DROPPED_BY_OWNER_RESCOPE |
| 38 | `AV1T-O1M-GC__2024-04-01_2024-10-01` | ohlcv-1m | 2024-04-01..2024-10-01 | — | 0 B | 0 B | $0.0000 | $21.3523 | — | DROPPED_BY_OWNER_RESCOPE |
| 39 | `AV1T-O1M-GC__2024-10-01_2025-04-01` | ohlcv-1m | 2024-10-01..2025-04-01 | — | 0 B | 0 B | $0.0000 | $21.3523 | — | DROPPED_BY_OWNER_RESCOPE |
| 40 | `AV1T-O1M-GC__2025-04-01_2025-10-01` | ohlcv-1m | 2025-04-01..2025-10-01 | — | 0 B | 0 B | $0.0000 | $21.3523 | — | DROPPED_BY_OWNER_RESCOPE |
| 41 | `AV1T-O1M-GC__2025-10-01_2026-04-01` | ohlcv-1m | 2025-10-01..2026-04-01 | — | 0 B | 0 B | $0.0000 | $21.3523 | — | DROPPED_BY_OWNER_RESCOPE |
| 42 | `AV1T-O1M-GC__2026-04-01_2026-10-01` | ohlcv-1m | 2026-04-01..2026-10-01 | — | 0 B | 0 B | $0.0000 | $21.3523 | — | DROPPED_BY_OWNER_RESCOPE |
| 43 | `AV1T-O1M-NQ__2023-10-01_2024-04-01` | ohlcv-1m | 2023-10-01..2024-04-01 | 250,008→250,008, 0.0% | 4,005,103 B | 4,063,797 B | $0.9127 | $22.2651 | PASS | MIRRORED |
| 44 | `AV1T-O1M-NQ__2024-04-01_2024-10-01` | ohlcv-1m | 2024-04-01..2024-10-01 | 267,558→267,558, 0.0% | 4,371,646 B | 4,216,886 B | $0.9768 | $23.2418 | PASS | MIRRORED |
| 45 | `AV1T-O1M-NQ__2024-10-01_2025-04-01` | ohlcv-1m | 2024-10-01..2025-04-01 | 262,462→262,462, 0.0% | 4,333,661 B | 4,034,712 B | $0.9582 | $24.2000 | PASS | MIRRORED |
| 46 | `AV1T-O1M-NQ__2025-04-01_2025-10-01` | ohlcv-1m | 2025-04-01..2025-10-01 | 254,244→254,244, 0.0% | 4,242,968 B | 4,487,161 B | $0.9282 | $25.1282 | PASS | MIRRORED |
| 47 | `AV1T-O1M-NQ__2025-10-01_2026-04-01` | ohlcv-1m | 2025-10-01..2026-04-01 | 261,836→261,836, 0.0% | 4,392,414 B | 3,998,157 B | $0.9559 | $26.0841 | PASS | MIRRORED |
| 48 | `AV1T-O1M-NQ__2026-04-01_2026-10-01` | ohlcv-1m | 2026-04-01..2026-10-01 | 273,492→273,492, 0.0% | 4,718,610 B | 4,607,917 B | $0.9985 | $27.0826 | PASS | MIRRORED |
| 49 | `AV1T-O1M-SI__2023-10-01_2024-04-01` | ohlcv-1m | 2023-10-01..2024-04-01 | — | 0 B | 0 B | $0.0000 | $27.0826 | — | DROPPED_BY_OWNER_RESCOPE |
| 50 | `AV1T-O1M-SI__2024-04-01_2024-10-01` | ohlcv-1m | 2024-04-01..2024-10-01 | — | 0 B | 0 B | $0.0000 | $27.0826 | — | DROPPED_BY_OWNER_RESCOPE |
| 51 | `AV1T-O1M-SI__2024-10-01_2025-04-01` | ohlcv-1m | 2024-10-01..2025-04-01 | — | 0 B | 0 B | $0.0000 | $27.0826 | — | DROPPED_BY_OWNER_RESCOPE |
| 52 | `AV1T-O1M-SI__2025-04-01_2025-10-01` | ohlcv-1m | 2025-04-01..2025-10-01 | — | 0 B | 0 B | $0.0000 | $27.0826 | — | DROPPED_BY_OWNER_RESCOPE |
| 53 | `AV1T-O1M-SI__2025-10-01_2026-04-01` | ohlcv-1m | 2025-10-01..2026-04-01 | — | 0 B | 0 B | $0.0000 | $27.0826 | — | DROPPED_BY_OWNER_RESCOPE |
| 54 | `AV1T-O1M-SI__2026-04-01_2026-10-01` | ohlcv-1m | 2026-04-01..2026-10-01 | — | 0 B | 0 B | $0.0000 | $27.0826 | — | DROPPED_BY_OWNER_RESCOPE |
| 55 | `AV1T-O1M-6E__2026-01-01_2026-07-01` | ohlcv-1m | 2026-01-01..2026-07-01 | 277,893→277,893, 0.0% | 3,258,886 B | 3,471,760 B | $1.0145 | $28.0971 | PASS | MIRRORED |
| 56 | `AV1T-O1M-6E__2026-07-01_2026-10-01` | ohlcv-1m | 2026-07-01..2026-10-01 | 125,576→125,576, 0.0% | 1,445,030 B | 1,718,350 B | $0.4585 | $28.5556 | PASS | MIRRORED |
| 57 | `AV1T-O1M-6J__2026-01-01_2026-07-01` | ohlcv-1m | 2026-01-01..2026-07-01 | 250,506→250,506, 0.0% | 2,755,784 B | 3,153,208 B | $0.9145 | $29.4701 | PASS | MIRRORED |
| 58 | `AV1T-O1M-6J__2026-07-01_2026-10-01` | ohlcv-1m | 2026-07-01..2026-10-01 | 121,508→121,508, 0.0% | 1,360,294 B | 1,628,858 B | $0.4436 | $29.9137 | PASS | MIRRORED |
| 59 | `AV1T-O1M-6A__2026-04-01_2026-10-01` | ohlcv-1m | 2026-04-01..2026-10-01 | 209,370→209,370, 0.0% | 2,395,902 B | 2,704,385 B | $0.7644 | $30.6781 | PASS | MIRRORED |
| 60 | `AV1T-O1M-6B__2026-04-01_2026-10-01` | ohlcv-1m | 2026-04-01..2026-10-01 | 195,349→195,349, 0.0% | 2,099,170 B | 2,476,933 B | $0.7132 | $31.3913 | PASS | MIRRORED |
| 61 | `AV1T-O1M-CL__2025-10-01_2026-01-01` | ohlcv-1m | 2025-10-01..2026-01-01 | — | 0 B | 0 B | $0.0000 | $31.3913 | — | DROPPED_BY_OWNER_RESCOPE |
| 62 | `AV1T-O1M-CL__2026-01-01_2026-04-01` | ohlcv-1m | 2026-01-01..2026-04-01 | — | 0 B | 0 B | $0.0000 | $31.3913 | — | DROPPED_BY_OWNER_RESCOPE |
| 63 | `AV1T-O1M-CL__2026-04-01_2026-07-01` | ohlcv-1m | 2026-04-01..2026-07-01 | — | 0 B | 0 B | $0.0000 | $31.3913 | — | DROPPED_BY_OWNER_RESCOPE |
| 64 | `AV1T-O1M-CL__2026-07-01_2026-10-01` | ohlcv-1m | 2026-07-01..2026-10-01 | — | 0 B | 0 B | $0.0000 | $31.3913 | — | DROPPED_BY_OWNER_RESCOPE |
| 65 | `AV1T-O1M-NG__2025-10-01_2026-01-01` | ohlcv-1m | 2025-10-01..2026-01-01 | — | 0 B | 0 B | $0.0000 | $31.3913 | — | DROPPED_BY_OWNER_RESCOPE |
| 66 | `AV1T-O1M-NG__2026-01-01_2026-04-01` | ohlcv-1m | 2026-01-01..2026-04-01 | — | 0 B | 0 B | $0.0000 | $31.3913 | — | DROPPED_BY_OWNER_RESCOPE |
| 67 | `AV1T-O1M-NG__2026-04-01_2026-07-01` | ohlcv-1m | 2026-04-01..2026-07-01 | — | 0 B | 0 B | $0.0000 | $31.3913 | — | DROPPED_BY_OWNER_RESCOPE |
| 68 | `AV1T-O1M-NG__2026-07-01_2026-10-01` | ohlcv-1m | 2026-07-01..2026-10-01 | — | 0 B | 0 B | $0.0000 | $31.3913 | — | DROPPED_BY_OWNER_RESCOPE |
| 69 | `AV1R-O1M-NQ-DELTA__2010-06-06_2012-06-01` | ohlcv-1m | 2010-06-06..2012-06-01 | 728,230→728,230, 0.0% | 9,588,257 B | 8,694,729 B | $2.6586 | $34.0499 | PASS | MIRRORED |
| 70 | `AV1R-O1M-NQ-DELTA__2012-06-01_2014-06-01` | ohlcv-1m | 2012-06-01..2014-06-01 | 721,912→721,912, 0.0% | 9,401,500 B | 8,904,131 B | $2.6355 | $36.6854 | PASS | MIRRORED |
| 71 | `AV1R-O1M-NQ-DELTA__2014-06-01_2016-06-01` | ohlcv-1m | 2014-06-01..2016-06-01 | 785,102→785,102, 0.0% | 10,891,196 B | 9,562,144 B | $2.8662 | $39.5517 | PASS | MIRRORED |
| 72 | `AV1R-O1M-NQ-DELTA__2016-06-01_2018-06-01` | ohlcv-1m | 2016-06-01..2018-06-01 | 869,202→869,202, 0.0% | 11,958,076 B | 10,516,405 B | $3.1733 | $42.7249 | PASS | MIRRORED |
| 73 | `AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01` | ohlcv-1m | 2018-06-01..2020-06-01 | 944,290→944,290, 0.0% | 14,359,255 B | 11,929,971 B | $3.4474 | $46.1723 | PASS | MIRRORED |
| 74 | `AV1R-O1M-NQ-DELTA__2020-06-01_2022-06-01` | ohlcv-1m | 2020-06-01..2022-06-01 | 1,024,386→1,024,386, 0.0% | 16,300,446 B | 13,662,792 B | $3.7398 | $49.9121 | PASS | MIRRORED |
| 75 | `AV1R-O1M-NQ-DELTA__2022-06-01_2023-10-01` | ohlcv-1m | 2022-06-01..2023-10-01 | 687,598→687,598, 0.0% | 11,131,265 B | 9,413,471 B | $2.5103 | $52.4224 | PASS | MIRRORED |
| 76 | `AV1R-O1M-ES-DELTA__2010-06-06_2012-06-01` | ohlcv-1m | 2010-06-06..2012-06-01 | 928,363→928,363, 0.0% | 11,450,868 B | 10,123,672 B | $3.3893 | $55.8117 | PASS | MIRRORED |
| 77 | `AV1R-O1M-ES-DELTA__2012-06-01_2014-06-01` | ohlcv-1m | 2012-06-01..2014-06-01 | 966,777→966,777, 0.0% | 11,433,219 B | 10,140,195 B | $3.5295 | $59.3412 | PASS | MIRRORED |
| 78 | `AV1R-O1M-ES-DELTA__2014-06-01_2016-06-01` | ohlcv-1m | 2014-06-01..2016-06-01 | 1,045,855→1,045,855, 0.0% | 12,847,282 B | 11,156,683 B | $3.8182 | $63.1593 | PASS | MIRRORED |
| 79 | `AV1R-O1M-ES-DELTA__2016-06-01_2018-06-01` | ohlcv-1m | 2016-06-01..2018-06-01 | 1,079,859→1,079,859, 0.0% | 12,785,806 B | 11,401,285 B | $3.9423 | $67.1017 | PASS | MIRRORED |
| 80 | `AV1R-O1M-ES-DELTA__2018-06-01_2020-06-01` | ohlcv-1m | 2018-06-01..2020-06-01 | 1,128,545→1,128,545, 0.0% | 14,511,055 B | 12,562,964 B | $4.1201 | $71.2218 | PASS | MIRRORED |
| 81 | `AV1R-O1M-ES-DELTA__2020-06-01_2022-06-01` | ohlcv-1m | 2020-06-01..2022-06-01 | 1,104,761→1,104,761, 0.0% | 15,103,065 B | 13,117,312 B | $4.0332 | $75.2550 | PASS | MIRRORED |
| 82 | `AV1R-O1M-ES-DELTA__2022-06-01_2023-10-01` | ohlcv-1m | 2022-06-01..2023-10-01 | 758,692→758,692, 0.0% | 10,450,223 B | 9,157,334 B | $2.7698 | $78.0248 | PASS | MIRRORED |
| 83 | `AV1R-O1M-6E-BACKFILL__2022-01-01_2024-01-01` | ohlcv-1m | 2022-01-01..2024-01-01 | 990,221→990,221, 0.0% | 12,371,393 B | 11,608,970 B | $3.6151 | $81.6399 | PASS | MIRRORED |
| 84 | `AV1R-O1M-6E-BACKFILL__2024-01-01_2026-01-01` | ohlcv-1m | 2024-01-01..2026-01-01 | 1,091,656→1,091,656, 0.0% | 12,850,424 B | 12,186,895 B | $3.9854 | $85.6253 | PASS | MIRRORED |
| 85 | `AV1R-O1M-6J-BACKFILL__2022-01-01_2024-01-01` | ohlcv-1m | 2022-01-01..2024-01-01 | 906,730→906,730, 0.0% | 10,968,697 B | 10,550,409 B | $3.3103 | $88.9356 | PASS | MIRRORED |
| 86 | `AV1R-O1M-6J-BACKFILL__2024-01-01_2026-01-01` | ohlcv-1m | 2024-01-01..2026-01-01 | 1,028,939→1,028,939, 0.0% | 11,976,911 B | 11,097,692 B | $3.7564 | $92.6920 | PASS | MIRRORED |
| 87 | `AV1R-O1M-6B-BACKFILL__2022-01-01_2024-01-01` | ohlcv-1m | 2022-01-01..2024-01-01 | 812,085→812,085, 0.0% | 9,549,429 B | 8,858,909 B | $2.9647 | $95.6568 | PASS | MIRRORED |
| 88 | `AV1R-O1M-6B-BACKFILL__2024-01-01_2026-01-01` | ohlcv-1m | 2024-01-01..2026-01-01 | 831,286→831,286, 0.0% | 9,154,730 B | 9,057,602 B | $3.0348 | $98.6916 | PASS | MIRRORED |
| 89 | `AV1R-O1M-6B-BACKFILL__2026-01-01_2026-04-01` | ohlcv-1m | 2026-01-01..2026-04-01 | 107,400→107,400, 0.0% | 1,205,004 B | 1,395,182 B | $0.3921 | $99.0837 | PASS | MIRRORED |
| 90 | `AV1R-O1M-6A-BACKFILL__2022-01-01_2024-01-01` | ohlcv-1m | 2022-01-01..2024-01-01 | 843,632→843,632, 0.0% | 10,469,494 B | 9,394,609 B | $3.0799 | $102.1636 | PASS | MIRRORED |
| 91 | `AV1R-O1M-6A-BACKFILL__2024-01-01_2026-01-01` | ohlcv-1m | 2024-01-01..2026-01-01 | 883,735→883,735, 0.0% | 10,247,200 B | 9,712,629 B | $3.2263 | $105.3899 | PASS | MIRRORED |
| 92 | `AV1R-O1M-6A-BACKFILL__2026-01-01_2026-04-01` | ohlcv-1m | 2026-01-01..2026-04-01 | 115,085→115,085, 0.0% | 1,388,296 B | 1,575,853 B | $0.4202 | $105.8101 | PASS | MIRRORED |

**Totals (rescope package): committed $105.8101 of the **$105.8101** rescope quote; lane hard stop $118.00; owner ceiling $125.00.**
- Chunks: 92 planned; 72 MIRRORED; states {"MIRRORED": 72, "DROPPED_BY_OWNER_RESCOPE": 20}.
- Records actually downloaded+QA'd: 106,053,893; raw .dbn.zst bytes on disk: 1,751,407,004; parquet bytes: 937,624,037.
- QA: 72 PASS, 0 FAIL.

## Budget accounting

| item | USD |
|---|---|
| chosen trim manifest quote | $113.0460 |
| committed (submitted+) at report time | $105.8101 |
| delivered (downloaded+) at report time | $105.8101 |
| lane hard stop | $118.0000 |
| owner ceiling | $125.0000 |
| headroom quote→hard stop | $4.9540 |

Billing basis: get_cost per exact chunk params before every submit (recorded in COMPLETION_LEDGER.json with timestamps); vendor bills delivered batch files on the same per-GB metered pricing (client docstring). Actual invoice reconciliation vs usage page is owner-side (NOT_RUN_DOC_UNCLEAR: no account endpoint).

## Disk

- start free: 21.412 GB decimal (2026-10-02, statvfs); reserve 20% = 4.282 GB; concurrent NONPRICE lane allowance 2 GB.
- per-batch gate in pipeline (raw+parquet+scratch+mirror vs free); measured ratios evolve in ledger disk_gate lines.
- raw zstd/billable measured (delivered so far): see ledger disk_gate fields; def chunks ≈0.034 (definitions compress ~30x).

## iCloud mirror

- Destination: `~/Library/Mobile Documents/com~apple~CloudDocs/my-quantitative-futures/av1-trim/`
- 72 chunks mirrored: raw .dbn.zst + parquet + qa.json + ledger entry per chunk; every copy SHA256-verified against source; state COPIED, cloud upload SYNC_PENDING_UNVERIFIED (macOS/iCloud's job — never claimed cloud-stored by this lane).
- This is the owner's personal backup of licensed data; no redistribution.

## Vendor-emission conventions MEASURED on first real data (documented, not defects)

- definition schema: every instrument definition re-broadcast at each session open (same ts_event, ts_recv = session start) + spread legs as separate records (leg_index); stream strictly ts_recv-ordered; with leg_index keyed: 0 duplicates, 0 content conflicts (first chunk evidence in qa/…qa.json).
- Billing reconciles exactly: quoted records == delivered records on every chunk so far (drift 0.000%).

## IBKR-overlap validation (STEP 4)

### NQ
- Identity: 10/10 contracts def.expiration==IBKR lastTradeDate (100% pass=True)
- Daily close (RTH subset): n=None, median|diff|=None ticks, within-1-tick=None% (pass=False)
- Daily volume ratio vendor/IBKR: median=0.9674, in[0.9,1.1]=91.643% (pass=True)
- M1 grid: 100.0% on-grid (pass=True); IBKR M1 overlap bars=4806, median|diff|=0.0 ticks
- Settlement vs IBKR close: n=1631, median|diff|=0.0 ticks, within-1-tick=100.0% (pass=True)

### CL
- Identity: None/None contracts def.expiration==IBKR lastTradeDate (100% pass=None)
- Daily close (RTH subset): n=None, median|diff|=None ticks, within-1-tick=None% (pass=None)
- Daily volume ratio vendor/IBKR: median=None, in[0.9,1.1]=None% (pass=None)
- M1 grid: None% on-grid (pass=None); IBKR M1 overlap bars=None, median|diff|=None ticks
- Settlement vs IBKR close: n=None, median|diff|=None ticks, within-1-tick=None% (pass=None)


## Partial-state law

Every chunk's exact params + job id + SHA256 live in COMPLETION_LEDGER.json (SUBMITTED-first). Resume never resubmits a recorded job; a pre-submit dedupe scan (list_jobs exact-param match) guards the crash-between-submit-and-ledger window.
