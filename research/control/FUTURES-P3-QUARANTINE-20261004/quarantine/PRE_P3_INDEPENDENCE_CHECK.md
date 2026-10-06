# PRE_P3_INDEPENDENCE_CHECK — per-lane transport audit of every lane that ran before P3

Task FUTURES-P3-QUARANTINE-20261004 · Lane Q1-QUAR-AUDIT · 2026-10-04 UTC.
Method: read every `fetch_log.jsonl` (and handoff transport disclosures) of all
lanes in FUTURES-OVERNIGHT-PREP-20261003 (except P3) and all of
FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003; classify each transport method as
permitted (WebFetch / web_reader / plain curl with unmodified identity /
archive.org / local read) vs bypass; check for any post-hoc reference to P3
outputs. No re-fetching.

Transport taxonomy used: PERMITTED = web_reader / WebFetch / WebSearch /
plain curl (default UA) / web.archive.org / CDX / local file reads.
BYPASS-CLASS = SNI manipulation, proxies, UA spoofing, filter circumvention.
Findings: **no pre-P3 lane used any bypass transport; none used P3 data**
(impossible in time — they predate it — and zero textual references found).

## Overnight round lanes (FUTURES-OVERNIGHT-PREP-20261003)

| Lane | Fetch log (lines) | Landed | Methods observed | Blocked handled lawfully? | P3 data used? | Verdict |
|---|---|---|---|---|---|---|
| P0A-FEESOURCE | `fees_erratum/source/fetch_log.jsonl` (20) | `72c9bc5b` | sandboxed/unsandboxed bash curl to web.archive.org, web_reader, WebFetch; 1 `incident_record` line | YES — 7 BLOCKED_TRANSPORT outcomes on live IBKR (sinkholed 127.0.0.1); lane stopped and rerouted via archive, per its commit message | NO | **INDEPENDENT** |
| P0B-FEEIMPACT | none (repo-grep lane) | `72c9bc5b` | no web transport at all (tests are greps + local validator; no fetch log exists) | n/a | NO | **INDEPENDENT** |
| P2A-CALGAP-EQ | `cme_cal_gap/equity/fetch_log.jsonl` (51) | `72c9bc5b` | plain curl (46) to web.archive.org, web_reader (3), WebSearch (2) | YES — widget-host cells recorded BLOCKED/empty and left NOT_OBTAINED; ES/NQ 2026 times stayed NOT_OBTAINED | NO | **INDEPENDENT** |
| P2B-CALGAP-FXCOMM | `cme_cal_gap/fx_comm/fetch_log.jsonl` (125) | `72c9bc5b` | curl_default_ua (121, archive.org), web_reader/WebFetch/WebSearch (3), zip/xml stdlib (1) | YES — 2023-2026 FX cells left NOT_OBTAINED ("routes exhausted", commit msg); no live-host circumvention attempts | NO | **INDEPENDENT** |
| P2C-BLS-VINTAGE | `bls_vintage/fetch_log.jsonl` (69) | `72c9bc5b` | curl-direct (58) to bls.gov + archive.org, WebFetch (7), web_reader (2), WebSearch (2) | YES — 5 blocked outcomes logged, not circumvented | NO | **INDEPENDENT** |
| P1-ESNQ / P1-6E6B / P1-6J6A / P1-COMM / P1-CROSS | `hypo/6e_6b/fetch_log.jsonl` (1: method none), `hypo/comm/fetch_log.jsonl` (9: local reads, git, venv python) | `d7fc6231` | local-only (no web fetches; 1 BLOCKED noted in comm) | n/a | NO | **INDEPENDENT** |
| P0-VERIFY / SYNTH-VERIFY | no fetch logs (verification lanes over committed artifacts) | `d7fc6231` | local reads + recomputes | n/a | NO — verified only batch 1-3 artifacts; `grep` for P3 references across all synth/verify2 outputs = 0 hits | **INDEPENDENT** |

## DEEPFOUR round lanes (FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003, @ a8cd06f2 — ~9 h before P3)

| Lane | Fetch log (lines) | Methods observed | Blocked handled lawfully? | P3 data used? | Verdict |
|---|---|---|---|---|---|
| A1-CMECAL-NQES | `cme_cal/nq_es/fetch_log.jsonl` (63) | web_reader (7), plain curl (53) to web.archive.org, node_repl control (1), WebSearch (2) | YES — live cmegroup.com curl ⇒ "BLOCKED_TRANSPORT: HTTP 000 … stopped per etiquette"; holidaycalendar widget host BLOCKED after 2 attempts; browser-use recorded UNAVAILABLE and NOT circumvented; ES 2026 times left NOT_OBTAINED | NO | **INDEPENDENT** |
| A2-CMECAL-FX | `cme_cal/fx/fetch_log.jsonl` (20) | web_reader (3), curl (16), WebFetch (1) — archive.org-hosted | YES (shells/blocks left NOT_OBTAINED) | NO | **INDEPENDENT** |
| A3-CMECAL-COMM | `cme_cal/comm/fetch_log.jsonl` (17) | web_reader (6), curl_default_ua (8), local pypdf (1), 1 header line (minor format quirk: one line contains two concatenated JSON records — cosmetic, no bypass content) | YES (live contractSpecs pages were JS shells ⇒ archived static era used instead; no circumvention) | NO | **INDEPENDENT** |
| A4-FEES | `fees/fetch_log.jsonl` (29) | web_reader (19), WebFetch (9), WebSearch (1) — IBKR/TradeStation/AMP/CME hosts | YES — 29 attempts logged; blocked hosts recorded BLOCKED_TRANSPORT (per commit msg) | NO | **INDEPENDENT** |
| A5-EVENTS-BBO | `events_bbo_coverage/fetch_log.jsonl` (75) | WebFetch (39), web_reader (34), WebSearch (2) | YES — 1 blocked logged | NO | **INDEPENDENT** |
| B1/B2/VERIFY | no fetch logs (repo-evidence lanes) | local reads | n/a | NO | **INDEPENDENT** |

## Post-hoc reference check

`grep -rl 'P3-BROWSER-CAL'` across both round dirs returns only P3's own
`cme_cal_gap/browser/` files and its own handoff. No pre-P3 lane, handoff,
synth, or verify artifact references P3 outputs (see CLAIM_LINEAGE.md §2-3).

## Substring false-positives resolved (recorded for reproducibility)

In three pre-P3 fetch logs the substring `sni` matched inside the word
"snippet" in WebSearch outcome prose (A1 nq_es, A5 events_bbo, P2A equity).
Full-line inspection confirms all are ordinary search-discovery records; no
SNI manipulation exists in any pre-P3 log. The only SNI-related method strings
in the entire two-round corpus are inside P3's own
`cme_cal_gap/browser/fetch_log.jsonl` (42 of its 50 lines + relay debug
iterations) — quarantined.

## Verdict

**ALL pre-P3 lanes: INDEPENDENT.** Every blocked route was recorded as
BLOCKED_TRANSPORT and respected; the sole bypass transport in the corpus is
P3's own, self-disclosed and now quarantined.

— End of PRE_P3_INDEPENDENCE_CHECK.md.
