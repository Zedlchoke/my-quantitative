# Task 0 — STOP before G1–G7

Verdict: **STOP (prompt branch b)**. The requested mirror criterion occurs in game 401909846 **and two additional games** (401909845, 401909847). This is the prompt's explicit stop condition. It is a screening signal, not proof that `nba26_predict` swapped home and away: the byte-pinned replay of 401909846 identifies Washington as home throughout.

## Frozen replay

- Production ledger: `/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1/ledger/paper_ledger.jsonl`; FORECAST row for 401909846 recorded 2026-10-22T13:50:12Z, anchor 2026-10-23T13:50:00Z, model `nba26_predict@57f0c810f8cd`, state prefix `2c1ac83afee477b8`, `HOME=0.6433001912350018`.
- Frozen source: `scoreboard_20261023.json` in the pinned NBA corpus, fetched 2026-10-22T13:50:12Z, SHA-256 `fc28f4c479ab1b9e81fd3cebce7b6a37c83853a3023769f8cc81747b757ce2d7`; corpus manifest verification returned OK. The event's ESPN competitor fields are `homeAway=home`, team ID 27, Washington Wizards; `homeAway=away`, team ID 28, Toronto Raptors. The loader passes `home_id=27`, `away_id=28` to the model.
- Pinned engine file SHA-256: `57f0c810f8cd1a12d78bcb68881ca49b6d8bdb16a4a0f61a11dfcc7987c6d81c`. Replaying completed rows strictly before the anchor gives Washington rating 1509.3865471034903 and Toronto rating 1506.9422255031832. The frozen `HCA=100`, divisor 400 formula returns HOME `0.6433001912350018`, identical to the ledger. State digest `2c1ac83afee477b8869c0f693175f6d5f0329b5ac4179ea379e0b8d9420b7097` also matches its recorded prefix. Thus the forecast is reproducible and its HOME label belongs to Washington.

## Cross-game comparison

The prompt calls this an 11-game slate, but its enumerated IDs `095`, `843–852`, `096` and the production ledger contain **12** games. All 12 were compared. ESPN projections below were fetched live from `site.api.espn.com/.../nba/summary?event=<id>` on 2026-10-23; their individual response hashes, fetch times, URLs, team IDs, and precise values are in `TASK0_PREDICTOR_PROBE_2026-10-23.json`. The ESPN field is `predictor.homeTeam.gameProjection`. PM HOME is the ledger's decimal odds and best ask from the 2026-10-22T13:50 quote. “Mirror” means `abs(model HOME − (1 − ESPN HOME)) < 0.03`.

| Event | Model HOME % | ESPN HOME % | PM HOME decimal | PM HOME ask | Mirror gap pp | Mirror? |
|---|---:|---:|---:|---:|---:|---|
| 401909095 | 76.05 | 56.5 | 1.778173 | 0.55 | 32.55 | No |
| 401909096 | 56.24 | 73.3 | 1.407460 | 0.70 | 29.54 | No |
| 401909843 | 53.80 | 50.4 | 2.210824 | 0.44 | 4.20 | No |
| 401909844 | 66.42 | 68.9 | 1.468310 | 0.67 | 35.32 | No |
| 401909845 | 59.75 | 40.8 | 2.030539 | 0.48 | 0.55 | Yes |
| 401909846 | 64.33 | 36.5 | 2.620167 | 0.37 | 0.83 | Yes |
| 401909847 | 55.17 | 44.7 | 1.810217 | 0.54 | 0.13 | Yes |
| 401909848 | 62.09 | 56.6 | 1.913894 | 0.51 | 18.69 | No |
| 401909849 | 66.74 | 64.0 | 1.633987 | 0.60 | 30.74 | No |
| 401909850 | 62.08 | 55.6 | 1.633987 | 0.60 | 17.68 | No |
| 401909851 | 60.66 | 73.9 | 1.252670 | 0.79 | 34.56 | No |
| 401909852 | 51.34 | 23.0 | 3.447325 | 0.28 | 25.66 | No |

ESPN's live projection for 846 is 36.5% HOME at this fetch, whereas the earlier audit quoted 35.2% HOME. The summary endpoint is live and these responses were not frozen at forecast time. Consequently the comparison satisfies the owner's operational stop rule but does not establish the root cause of the apparent cross-model mirror. The exact-home/away replay contradicts a simple assignment reversal in the frozen engine path.

## Boundary and next decision

No engine, collector, prompt, EV, stake, anchor, or allow-list code was changed; G1–G7 and battery/A7 were not run because the prompt required immediate STOP at Task 0. `AI_PROMPT_V3` registered digest, calculated by its digest-blanked freeze law, was `c2c4fd464f0413a054d94cb2f555f1e9325ed3b78111142b551026f3e2a0c890` in both main and fixall worktrees. The raw file SHA-256 is `0cdbd7be7543f5f628fbe00601490357d2f8248e0f4533141636f6f4fca22169`; this differs by design because the registered value is embedded in the file.

Owner adjudication is required before resuming G1–G7 or opening a separate engine repair cycle. The next diagnostic should freeze ESPN summary snapshots and inspect the other two apparent mirrors, without changing model law on this evidence alone.
