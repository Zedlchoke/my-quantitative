# Task 0B — frozen replay (PASS)

Owner 2026-10-23 09:15 ICT superseded the mirror heuristic used in Task 0. Task 0's frozen replay of 846 remains valid. This report uses the same pinned loader and engine, with no model-law changes, for 845 and 847.

The corpus manifest verifies `OK` at effective composite `501af5ec51cf971f07a282b9ec49e465d628c427352566e11baf2ee389541096`. Both games came from frozen `scoreboard_20261023.json`, SHA-256 `fc28f4c479ab1b9e81fd3cebce7b6a37c83853a3023769f8cc81747b757ce2d7`; the meta record says fetched 2026-10-22T13:50:12Z. Replay used anchor `2026-10-23T13:50:00Z`, completed games strictly before that time, and pinned `predict.py` SHA-256 `57f0c810f8cd1a12d78bcb68881ca49b6d8bdb16a4a0f61a11dfcc7987c6d81c`. Replayed state digest is `2c1ac83afee477b8869c0f693175f6d5f0329b5ac4179ea379e0b8d9420b7097` for both.

| Game | Frozen ESPN `homeAway` → loader IDs | Home rating | Away rating | Replayed HOME | Ledger HOME | Exact? | Equal-rating HCA-only HOME |
|---|---|---:|---:|---:|---:|---|---:|
| 401909845 | Orlando Magic `home` → 19; Minnesota Timberwolves `away` → 16 | 1493.0161495737962 | 1524.39044068391 | 0.5974957068827914 | 0.5974957068827914 | Yes | 0.6400649998028851 |
| 401909847 | Miami Heat `home` → 14; Detroit Pistons `away` → 8 | 1472.2445684719974 | 1536.225900707522 | 0.5516501258554483 | 0.5516501258554483 | Yes | 0.6400649998028851 |

The equal-rating reference is `1/(1+10^(-100/400))`. For 845 and 847 the away team's higher rating offsets part of the 100-point home-court advantage, yielding 59.75% and 55.17% HOME. Alongside the bit-exact 846 replay, this closes the home/away assignment suspicion for the shared slate code path under the owner's Task 0B gate. It does not assess model quality or change HCA/priors.
