# G1–G7 production adoption — STOPPED, NOT ACCEPTED

Owner GO: 2026-10-23 09:49 ICT. Integration was limited to the previously audited G1–G7 tree; no engine, HCA/prior, EV/stake/anchor, prompt, or G7-ii change.

## Step 1 — G2 live slug evidence

Raw probe summaries are in `g2_live_probes_2026-10-23/`, one JSON per configured competition. Each file records URL, HTTP status, response SHA-256, byte count and a real board event excerpt (event ID, date, both team names/IDs and homeAway). All checks were repeated at approximately 02:54Z on 2026-10-23.

| Config competition | ESPN slug | News | Board | Verified event |
|---|---|---:|---:|---|
| `soccer_uefa_nations_league` | `soccer/uefa.nations` | 200 | 200 | 401861093 |
| `soccer_fifa_world_cup_group` | `soccer/fifa.world` | 200 | 200 | 760415 |
| `soccer_uefa_euro_group` | `soccer/uefa.euro` | 200 | 200 | 690573 |
| `soccer_fifa_world_cup_qualifiers` | `soccer/fifa.worldq.uefa` | 200 | 200 | 724835 |
| `soccer_uefa_euro_qualifiers` | `soccer/uefa.euroq` | 200 | 200 | 655247 |

No slug failed this repeated probe. These are ESPN research paths, not claims that all five Odds API sport keys currently list markets.

## Step 2 — Root integration and verification

Integration worktree branch `orca/paperdesk-fixall-ncaa-v1-integration` was committed at `d62d22d3b732aa82b8e4763d775150bc2f9931a5` and root/main fast-forwarded from `27ae3bd73814cba3a78e1495d5899c6e1af70d89` to that exact commit. The commit includes `nba_injury_pdf.js` as a tracked file, all four changed Python modules, tests, Task 0/0B and A7 records. Pre-existing untracked owner instruction files were left untouched.

Root `research/papertrade_exec/ai_research.py` SHA-256 is exactly `28207b5a63da7c48baa4e0d9113d8fce7e84daaa61a4b61f247ff8d90f3e5ad2`, matching the A7-read integration collector. No merge conflict or code change to that file occurred. Root `git diff --check` returned 0. Registered `AI_PROMPT_V3` digest before and after is `c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890`.

Full root battery command: `.venv/bin/python -m pytest tests/papertrade_exec -q`; log saved verbatim as `ADOPTION_BATTERY_ROOT_2026-10-23.log`. Result: **323 passed, exit 0, 62.64 seconds**.

## Step 3 — Production restart

Before restart, production PID 8972 had cwd root and used old collector SHA `3608dff8d64e4b2a38e639a5a3d489e1f6350f1d2bec7792bb5e7f5a5511d437`. The 02:56Z heartbeat showed cadence actions `NONE` for every lane/date, 0 settle attempts, and no current decide. `ai_review/pending.json` held the older `FD-2026-M48` marker; its old quote has no PM walk/crosswalk. The next new WSL 25/10 window was not yet open.

SIGTERM to PID 8972 produced `SERVICE_STOP` at `2026-10-23T02:56:42Z`; process exited and released its singleton lock. The same production command was started from root with the root virtualenv and data root. New PID **15385** started at `2026-10-23T02:56:51Z` (09:56:51 ICT), cwd `/Users/hoangminhlong/my-quantitative`, `SERVICE_START` at `02:56:52Z`, and heartbeat tick 1 at `02:57:05Z` with all cadence actions `NONE`. A fresh import from the same root cwd resolves `ai_research.__file__` to root and SHA `28207b5a63da7c48baa4e0d9113d8fce7e84daaa61a4b61f247ff8d90f3e5ad2`. No rollback was needed. Runtime packet stamping remains to be confirmed by the first produced packet.

## Step 4 — First real post-adoption slate

The first real post-adoption slate is WSL 2026-10-25: forecasts at 2026-10-23T06:00:47Z, quotes at 06:00:51Z, followed by actual producer reviews and cadence decisions. Artifacts are retained under `evidence/adoption_g1_g7/wsl_20261025/`: 18 evidence packets (all attempts), five V3 journals, five opinions, relevant ledger rows, gate events and incidents, source counts and a SHA-256 manifest recording each copied raw file and original path. All 18 evidence stamps equal `28207b5a63da7c48baa4e0d9113d8fce7e84daaa61a4b61f247ff8d90f3e5ad2`. All five opinions carry `AI_PROMPT_V3` and the registered prompt digest.

| Candidate | Packet attempts | news_48h | injuries | gamma_event | league_official | official_injury_report | scoreboard_status |
|---|---:|---:|---:|---:|---:|---:|---:|
| FD-2026-M43 | 3 | 0 | 0 | 0 | 1 | 0 | 1 |
| FD-2026-M45 | 3 | 0 | 0 | 0 | 1 | 0 | 1 |
| FD-2026-M46 | 3 | 0 | 0 | 0 | 1 | 0 | 1 |
| FD-2026-M47 | 4 | 0 | 0 | 0 | 1 | 0 | 1 |
| FD-2026-M49 | 5 | 0 | 0 | 0 | 1 | 0 | 1 |

Counts shown are per packet; all repeated attempts for each candidate had these same counts. The `eng.w.1` scoreboard matched both fixture names and returned a genuine event, including M43 -> ESPN event 401902886. The official WSL page was fetched, but its excerpt is a loading/navigation shell with `team_name_hit=no`; its existence alone does not prove useful fixture context. Core injury endpoints reported `items=0 sources=0`.

Observed adoption gaps requiring independent review: every new WSL quote carries PM event identity in top-level `event_id` and depth/fee data in `pm_outcomes`. The audited collector/producer consumes `pm_crosswalk.pm_event_id` and `pm_walk.legs`, so all five new WSL candidates journal `gamma_event skipped: no gamma_event_url provided by caller`; market_block copies decimal odds but has null best_ask/vwap/depth/fee, omits DRAW, and no team_block. This is not evidence of a Polymarket transport failure. These new candidate rows are distinct from the owner's allowed old-M48 exception. No code fix was attempted under the adoption-only order.

NBA 24/10 has not entered its 24-hour lookahead window yet (expected around 15:50Z on 23/10). NBA Gamma, complete market/team payload, two rest/B2B checks and official PDF comparison remain NOT_RUN. The WSL packets are nonempty and missing Gamma is explicitly journaled, so no unexplained-empty-packet stop was inferred solely from this observation. An independent A7 review is being requested now to adjudicate the observed schema gaps before further acceptance work.

## Step 5 — Fresh A7 and coordinator review

The adoption evidence was committed as `25882fad8a31a5432f5f4fc5a848d302864a3e23` (documentation/artifacts only; runtime code remains the exact `d62d22d3` implementation). Fresh-context independent A7 audited this exact commit and confirmed **BUG / FAIL acceptance** in the new real WSL packets: the producer ignores the quote's known top-level event identity, the collector reads the wrong WSL PM field layout and drops DRAW, and WSL returns before producing any team_block. The Gamma skip journal records the caller symptom; it does not establish a provider outage or an absent event identity. These are proven WSL data omissions, separate from the still-NOT_RUN NBA checks.

Under the original prompt's A7-BUG stop condition, adoption acceptance work stopped and automation `paperdesk-g1-g7-adoption-evidence` was set to **PAUSED**. No feature fix, law change, or additional production restart was performed. PID 15385 remained healthy on the adopted SHA at the last check. There was no startup/collector-load failure requiring rollback. The actual WSL slate had already produced two paper decisions (M47 DRAW and M46 AWAY); those append-only records were preserved. NBA Gamma/context/PDF/rest acceptance and coordinator reconciliation remain **NOT_RUN**. No G1–G7 acceptance verdict is claimed.

Formal independent report and structured handoff: `a7_adoption/A7_ADOPTION_VERDICT_2026-10-23.md` (SHA-256 `10b539ae9cb6b7ff62b66f899ac61b576a2544a3905d3c2c4f168f9b3fddfa2f`), `a7_adoption/audit_checks.json`, and `a7_adoption/handoff.json`. A7 confirmed the implementation/helper/prompt identity, saved G2 probes, all 28 copied raw-file manifest hashes and the root battery log. It classified three HIGH schema/context BUGs and the official-page shell as a MED acceptance gap. The current adoption order authorizes no additional feature changes; owner disposition is required for remediation after this stop.
