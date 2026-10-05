# ERRATUM R1 — Canonical team-key lineage rebranch (Lane A, WNBA-WINPROB-PREP-V1)

- task `wbap-a-data-r1` · cycle `WNBA-WINPROB-PREP-V1` · role quant-implementer · 2026-10-05
- Scope: EXTEND-ONLY remediation of the lane-A artifacts flagged in
  `lanes/D_VERIFY/VERIFICATION_REPORT.md` (verdict VERIFICATION_FAIL, D-1 MAJOR + D-2/D-3/D-4 MINOR).
  No commits (controller lands). Write scope honored: `lanes/A_DATA/**` +
  `~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv` (+ regenerated
  `measurements_a2.json`). Lanes B/C/D untouched; corpus read-only.
- Base: branch `orca/wnba-winprob-prep-v1-integration`, HEAD measured
  `448710a659263e2b9ecda693224c8ab8d577fdba` (controller's post-verification landing; lane
  A/B/C bytes identical to the verifier's measured HEAD `18fa135b…` — the landing commit added
  lane D files only). All numbers below re-measured from corpus bytes with
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`. Schema/coverage counting only.

---

## 1. What was wrong (verifier's finding, quoted)

> "**FAIL — D-1 (MAJOR): the canonical team-key table resolves the flagged lineage conflict on
> the wrong branch.** `team_key_table.csv` (and SPEC §2) encode: `SAN_DAL` = {UTA, SAN, DAL},
> seasons 1997–2026 continuous, with the spec text 'SAN … 2003–2015 → DAL Dallas Wings 2016–'
> and '2016 overlap SAN+DAL is the merger season'; `DET_TUL` = {DET, TUL}, seasons **1998–2015
> (terminated)**; `LVA` = separate franchise 2018–2026 with **no prior stream**.
> Measured bytes refute the table's own text: **San Antonio rows exist in 2016 AND 2017**
> (San Antonio Stars = 2014–2017), and SAN + DAL coexist as two of 12 distinct teams in both
> 2016 and 2017 — a single franchise cannot continue SAN→DAL across two seasons of coexistence.
> … The spec is also internally contradictory: its own `LVA` row says 'SAS→LVA relocation: SAN
> last season 2017, LVA first 2018' while the `SAN_DAL` row ends SAN at 2015 and rebrands it
> DAL. Consequence …: the successor's B1 stream map would give Dallas the Utah/San Antonio
> history, terminate the Tulsa stream, and cold-start Las Vegas — wrong on all three counts."

## 2. What the data shows (re-measured for this erratum)

### 2a. Stats-side abbreviation presence, season by season (affected franchises)

| stats abbr | display name(s) | seasons present | rows total |
|---|---|---|---|
| UTA | Utah Starzz | 1997–2002 (6) | 193 (28, 30, 32, 32, 34, 37) |
| SAN | San Antonio Silver Stars **2003–2013**, San Antonio Stars **2014–2017** | **2003–2017 (15)** | 536 (34, 34, 34, 34, 39, 43, 37, 36, 37, 36, 34, 36, 34, **34, 34**) |
| LVA | Las Vegas Aces | **2018–2026 (9)** | 384 |
| DET | Detroit Shock | 1998–2009 (12) | 445 |
| TUL | Tulsa Shock | 2010–2015 (6) | 206 |
| DAL | Dallas Wings | **2016–2026 (11)** | 408 |
| LAS | Los Angeles Sparks | **1997–2026 (30), continuous** | 1,111 |

### 2b. The coexistence that kills the merger story

Distinct stats abbreviations per season (league census):

| season | distinct abbrs | contains SAN | contains DAL | contains TUL | contains LVA |
|---|---|---|---|---|---|
| 2015 | 12 | yes | no | yes (last TUL season) | no |
| 2016 | 12 | **yes** (34 rows) | **yes** (34 rows) | no | no |
| 2017 | 12 | **yes** (34 rows) | **yes** (35 rows) | no | no |
| 2018 | 12 | no | yes | no | yes (first LVA season) |

SAN and DAL coexist as 2 of 12 teams in BOTH 2016 and 2017 → the 2016 TUL→DAL rebrand and the
2018 SAN→LVA relocation are independent events; DAL cannot be the SAN successor.

### 2c. ESPN side of the same franchises

| ESPN display name | rows | seasons | ESPN abbr(s) observed |
|---|---|---|---|
| Detroit Shock | 318 | 2002–2009 | **`TUL` on every row, home AND away** (per season: 2002:32, 2003:42, 2004:37, 2005:36, 2006:44, 2007:45, 2008:43, 2009:39); abbreviation `DET` appears **0** times on ESPN |
| Tulsa Shock | 206 | 2010–2015 | `TUL` |
| Dallas Wings | 409 | 2016–2026 | `DAL` |
| Utah Starzz | 36 | 2002 | `UTH` |
| San Antonio Silver Stars | 397 | 2003–2013 | `SA`, `SAS` |
| San Antonio Stars | 138 | 2014–2017 | `SA` |
| Las Vegas Aces | 392 | 2018–2026 | `LV` |
| Los Angeles Sparks | 941 | 2002–2026 | `LA`, `LOS` |

Note: ESPN's Detroit rows per season (32/42/37/36/44/45/43/39) equal the stats DET rows
per season exactly — same games, mislabeled key.

## 3. Corrected lineage (normative, data-verified)

```
LVA  :=  UTA Utah Starzz 1997–2002 → SAN San Antonio Silver Stars 2003–2013 /
         San Antonio Stars 2014–2017 → LVA Las Vegas Aces 2018–2026
DAL  :=  DET Detroit Shock 1998–2009 → TUL Tulsa Shock 2010–2015 → DAL Dallas Wings 2016–2026
LAS  :=  continuous 1997–2026 (never relocates)
```

## 4. What changed

### 4a. `~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv` (before → after)

Removed rows (wrong branch):

```
SAN_DAL,Dallas Wings; San Antonio Silver Stars; San Antonio Stars; Utah Starzz,DAL; SAN; UTA,Dallas Wings; San Antonio Silver Stars; San Antonio Stars; Utah Starzz,DAL; SA; SAS; UTH,1997,2026
DET_TUL,Detroit Shock; Tulsa Shock,DET; TUL,Detroit Shock; Tulsa Shock,TUL,1998,2015
LVA,Las Vegas Aces,LVA,Las Vegas Aces,LV,2018,2026
```

Added rows (correct branch; franchise_key is the modern key of the lineage):

```
LVA,Las Vegas Aces; San Antonio Silver Stars; San Antonio Stars; Utah Starzz,LVA; SAN; UTA,Las Vegas Aces; San Antonio Silver Stars; San Antonio Stars; Utah Starzz,LV; SA; SAS; UTH,1997,2026
DAL,Dallas Wings; Detroit Shock; Tulsa Shock,DAL; DET; TUL,Dallas Wings; Detroit Shock; Tulsa Shock,DAL; TUL,1998,2026
```

Net: 21 → **20** franchise keys. The `DAL` row's `espn_abbrs_observed` = {DAL, TUL} — TUL from
the 2010–2015 Tulsa rows AND the mislabeled 2002–2009 Detroit rows (§2c), itself a live
demonstration of the "never join on raw ESPN abbreviations" law.

### 4b. `measurements_a2.json` — regenerated via `measure_a2.py` (which encoded the wrong map)

`measure_a2.py` edits: `FRANCHISE_OF_NAME` rebranched (Utah/San Antonio/Las Vegas → `LVA`;
Detroit/Tulsa/Dallas → `DAL`); dead `FRANCHISE_KEY_OUT` updated; Cup-final detector fixed (D-4,
below). Full re-run diff vs the pre-erratum output (backup diff-verified):

| block | before | after |
|---|---|---|
| `team_key_table` | keys incl. `SAN_DAL`, `DET_TUL`, standalone `LVA` | keys `LVA` (UTA/SAN/LVA eras, seasons 1997–2026) + `DAL` (DET/TUL/DAL eras, seasons 1998–2026) |
| `team_key_table_rows` | 21 | **20** |
| `espn_commissioners_cup.rows_championship` | 7 | **6** |
| `espn_commissioners_cup.championship_by_season[2024]` | 2 | **1** |
| `espn_commissioners_cup.championship_neutral_site_rows` | 2 | **1** |

**Every other block reproduces unchanged** (identity, 0-0/forfeit/postponed law, 21 alias rows,
7 TBD, 16 neutral, 301 Cup rows, per-season census 5,988/7,008/union 7,017, timestamp laws,
row-level join 5,954+25 / 9 / 1,029): top-level keys identical; diff shows only the three blocks
above. The census/join never depended on the franchise map (they key on display names), so no
universe number moves. The team_key CSV rows are written by the same script run.

### 4c. `GAME_UNIVERSE_SPEC_WNBA_1997PLUS.md` — surgical edits only

- §2: ERRATUM pointer note; "21 franchise keys" → "20 franchise keys"; `SAN_DAL` / `DET_TUL` /
  standalone `LVA` rows replaced by the two corrected lineage rows (§3 above, with the
  coexistence evidence); LAS row now states continuity explicitly.
- §2 "Never join" paragraph: DET/TUL mislabel scope corrected from "ESPN's 2002 file labels all
  16 Detroit Shock rows" to **all ESPN seasons 2002–2009, 318 rows, home and away, `DET` 0
  times** (verifier D-2, MINOR).
- §4 item 3: measured per-token alias breakdown added (verifier D-3, MINOR) — EAST 11, WEST 11,
  USA 4 (2004/2010/2021/2024), **WIL 3 (2019/2022/2023)**, ALL 3, **STE 2 (2022/2023)**,
  DEL 2 (2018/2019), PAR 1, COL 1, CLA 1, SPO 1, COOP 1. Honesty note: the 13-token set on disk
  (spec §4 item 3, `measure_a2.py`, handoff_A.json) already contained `WIL`/`STE` — re-grepped
  and re-read at r1 start; the defect is closed by making the normative list byte-verifiable
  with the measured per-token rows, exactly as the remediation instruction required.
- §4 item 6: Cup finals 7 → **6** (verifier D-4, MINOR) with the six finals enumerated by ET
  date/home/away/headline and the detector cause named; §4 item 5's "Cup finals are neutral"
  clause corrected (only 2021/2025/2026 finals are neutral; 2022–2024 finals were home games).
- No other section touched (§1, §3, §5–§10 unchanged; §5/§6 already carried the correct 6-finals
  arithmetic and now agree with §4).

### 4d. The six Cup finals (measured; replaces the double-counted 7)

| Cup season | ET date | home vs away | headline | neutral |
|---|---|---|---|---|
| 2021 | 2021-08-12 | SEA vs CON | "WNBA Commissioner's Cup" (plain) | yes |
| 2022 | 2022-07-26 | CHI vs LVA | "…Cup Championship" | no |
| 2023 | 2023-08-15 | LVA vs NYL | "…Cup Championship" | no |
| 2024 | 2024-06-25 | NYL vs MIN | "…Cup Championship" | no |
| 2025 | 2025-07-01 | MIN vs IND | "…Cup Championship" | no |
| 2026 | 2026-06-30 | NYL vs LVA | "…Cup Championship" | no |

Cross-check: in every Cup season the final is the last-scheduled Cup game. The prior "7" came
from lane A's `cup_champ` detector ("Cup" AND neutral-site) additionally catching the
**2024-06-06 Chicago Sky @ Washington Mystics neutral Cup GROUP game** — a real regular-season
game, still counted in the 301 Cup rows and 16 neutral rows, never a final. The detector in
`measure_a2.py` is fixed accordingly.

## 5. Lane C (D-5) — deliberately untouched

`lanes/C_PROTOCOL/**` verbatim-inherit sections still carry the stale prior-memo counts
(15 neutral rows vs measured 16; 14 All-Star rows / incomplete alias set vs measured 21 rows /
13-token set — 11 rows would leak: USA×4, WIL×3, STE×2, COL×1, SPO×1). Per remediation
instruction this is NOT edited here; it is a **known limitation for the successor to reconcile
at the B1 freeze** (lane C §12.4 re-verify clause already mandates that reconciliation).

## 6. Reproduction

```
git -C <worktree> rev-parse HEAD        # 448710a659263e2b9ecda693224c8ab8d577fdba
/Users/hoangminhlong/my-quantitative/.venv/bin/python lanes/A_DATA/measure_a2.py
                                        # regenerates measurements_a2.json + team_key_table.csv (read-only over corpus)
diff <backup> ~/.my-quantitative-data/wnba-prep-v1/measurements_a2.json
                                        # only team_key_table / team_key_table_rows / espn_commissioners_cup move
```

No win-prob metric computed anywhere; schema/coverage counting only. No network access.
