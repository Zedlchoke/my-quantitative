# Lane A2 dossier — CME Micro FX futures official-source canary (fxf-a2)

Cycle FX-FUTURES-FRONTIER-V1, branch `orca/fxf-a2`, base `06af8ba508a9e886f81da100c02d595915329a69`.
Subject (frozen, plan §2): exactly M6E, M6B, M6A, MCD, MJY. No other symbol.

## 1. What this lane did

1. Verified worktree/branch/HEAD, heartbeat, read the frozen plan at base.
2. Frose `canary_manifest.json` (09:24:50Z) BEFORE any content fetch: per-instrument
   canary set (product page, one recent settlement fetch, one historical sample),
   fee + margin documentation, legal pages, etiquette (sequential, ≥1 s, ≤2 retries,
   no concurrency), 300 MB byte cap, census law, block law.
3. Executed the first content fetch at 09:26:45Z — all five official product-page
   canaries failed with `curl: (7) Failed to connect to www.cmegroup.com port 443
   after 2 ms` — a connection-level refusal, 0 bytes.
4. Ran the prescribed SNI/destination-IP discrimination experiment (never bypassing):
   - Neutral controls from the same shell: example.com and google.com → HTTP 200.
     Environment egress is healthy; the refusal is not global confinement.
   - Local resolver (192.168.0.1 LAN DNS, NOT /etc/hosts — no cmegroup entry exists
     there): `www.cmegroup.com` → **127.0.0.1** (and ::1); `cmegroup.com` →
     23.66.152.172; `ftp.cmegroup.com` → 13.57.171.25. The sinkhole is host-selective.
   - DoH (dns.google and cloudflare-dns.com): authentic `www.cmegroup.com` is an
     Akamai edge (23.66.152.172 / 23.51.32.131 via `e5296.a.akamaiedge.net`). The
     local 127.0.0.1 answer is therefore a measured DNS sinkhole for that hostname.
   - Transport probe to the DoH-authentic IP with correct SNI `www.cmegroup.com`:
     **TLS connection reset by peer** (in-path SNI filtering).
   - Same-IP different-SNI control: the SAME Akamai IP completes TLS for a different
     SNI (cert-mismatch error, no reset) — the edge serves TLS generally; the filter
     kills SNI=`www.cmegroup.com` specifically.
   - Apex `https://cmegroup.com/`: TCP opens, then 0 bytes / 15 s timeout (drop).
   - `https://ftp.cmegroup.com/`: TCP SYN silently dropped, despite authentic DNS.
5. Frose `census_manifest.json`, then ran a 10-probe representative
   blocked-surface confirmation grid (5 instruments × sampled-years {2019, 2026}):
   every probe shows the identical connection-refused signature. The full
   ≥8×5×5 existence census is `NOT_RUN` — the surface it would prove existence on
   does not exist from this vantage, and missing evidence is never inferred.
6. Determinism: re-fetched all five phase-1 URLs; bodies are byte-identical 0-byte
   refusals (blocked-state reproduction ALL_MATCH 5/5, harness comparison bug
   disclosed and corrected in `determinism_refetch.json`). Content determinism is
   `NOT_RUN_TRANSPORT_BLOCKED` — there are no content bytes to re-hash.

## 2. Why the identity pack is empty (and must be)

Plan §4.1 and Q-8: every measured claim traces to fetched bytes or hashed official
pages. ZERO official CME bytes were obtainable. Every identity field (a)–(m) is
`NOT_RUN_TRANSPORT_BLOCKED` per instrument; the license class is
`UNAVAILABLE_FAIL_CLOSED` (no page to hash, no clause to quote verbatim, nothing
accepted on the owner's behalf). No third-party mirror, memory, or summary was
substituted for official bytes — that substitution is forbidden by §3.

## 3. Verdict

- Per instrument (all five): `SOURCE_DEAD_TRANSPORT_BLOCKED`.
- Lane verdict: **`BLOCKED_TRANSPORT`** (dispatch/plan §5, §7 rule 2 class).
- Content bytes downloaded: **0 / 300,000,000** cap.
- Bypass attempts: **none**. `--resolve` was used only as a classification probe
  with the body discarded, never as a data channel.

## 4. Owner-action input (no decision taken by this lane)

Unblocking the CME Group estate in this environment (DNS sinkhole of
`www.cmegroup.com` + in-path SNI filter + dropped apex/ftp transports) is an owner
decision per L-FIBV1-1. After a lawful unblock, lane a2 re-runs unchanged with the
same frozen manifests. Until then, per plan §7 rule 2, the cycle-level mapping
candidate is `BLOCKED_TRANSPORT` — adjudication belongs to the Lead/A7.

## 5. Incidents (same-session, §10)

`INC-FXFA2-1` transport block (the finding above); `INC-FXFA2-2` harness retry bug
on connection-refused (retries never fired in phase 1; block reproduced uniformly
in 21 later probes, so exposure is nil); `INC-FXFA2-3` harness saved 0-byte files
for failed fetches and the initial rehash comparison artifact `all_match=false`
(null vs empty-hash). All disclosed in `incident_record.json`.

## 6. Evidence index

`fetch_transcripts.jsonl` (37 rows: phase-1 fetches, P1–P5 discrimination probes,
in-band DoH + neutral-control + local-DNS re-measurements, census grid, rehash),
`transport_discrimination_experiment.json`, `census_manifest.json` +
`census_results.json`, `determinism_refetch.json`, `raw_byte_index.json`,
`identity_pack_{M6E,M6B,M6A,MCD,MJY}.json`, `license_evidence.json`,
`verdict.json`, `incident_record.json`, harness `lane_fetch.py`,
frozen `canary_manifest.json`. Raw bytes (0-byte refusal artifacts only) live
outside git at `/Users/hoangminhlong/.my-quantitative-data/fx-futures-frontier-v1/raw/lane-a2/`.
