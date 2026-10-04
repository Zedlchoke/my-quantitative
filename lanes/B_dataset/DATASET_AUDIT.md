# DATASET_AUDIT — nba-538-v1 (Lane B, NBA-WINPROB-PREP-V1)

- Audit date: 2026-10-04
- Auditor: Lane B (B_dataset), isolated lane; controller cross-checks artifacts.
- Input (read-only, outside git): `~/.my-quantitative-data/nba-538-v1/raw/nbaallelo.csv`
- Audit code: `audit_script.py` in this directory (stdlib+pandas, no network, no
  writes); follow-up queries reproduced in Appendix B.
- Attribution: see `~/.my-quantitative-data/nba-538-v1/raw/ATTRIBUTION.md`
  (FiveThirtyEight nba-elo, CC BY 4.0; game info from Basketball-Reference).
  Conditions: internal research only, no redistribution.

## 0. Verdict + headline numbers

**PASS with documented limitations.** The file is internally consistent to a very
high standard (every mirror check between the two rows of each game passes with
zero violations). Coverage ends **2015-06-16** (2015 Finals game 6); there are
**no rows after 2015-07-01** and the controller's tail hypothesis is confirmed:
this "Complete History" file ends with the 2014-15 season.

| Metric | Value |
|---|---|
| sha256 (re-verified) | `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc` MATCH |
| size | 18,173,265 bytes MATCH |
| data rows (excl. header) | 126,314 |
| games (distinct game_id) | 63,157 (each exactly 2 rows) |
| seasons (year_id) | 1947..2015 (69 seasons; 1947 = BAA 1946-47) |
| date range | 1946-11-01 .. 2015-06-16 (12,426 distinct dates) |
| regular-season games | 59,124 |
| playoff games | 4,033 |
| ABA games (lg_id=ABA, 1968-1976) | 4,149 |
| distinct team_id / fran_id | 104 / 53 |
| mirror violations (pts, elo, location, result, ids) | 0 of 63,157 games |
| seasons deviating >10% from era expectation | 0 |
| max games per day | 15 (30-team era) |
| home win rate (H-designated rows) | 0.6225 |
| 538 season-boundary Elo carryover (median, elo_n method) | 0.7542 |
| expansion-team cold start | elo_i = 1300.0 exactly (42 of 104 team_ids) |

---

## 1. File integrity (check 1)

```
$ shasum -a 256 nbaallelo.csv
d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc  nbaallelo.csv
```
Matches ATTRIBUTION.md and DATA_MANIFEST.md. Python re-hash of the byte stream
also matched. Header: 23 columns (incl. `seasongame`, as flagged by controller).
All 126,314 data rows parse with `%m/%d/%Y` dates; zero parse failures.

## 2. Column census (check 2)

| column | dtype | nulls | n_unique | notes |
|---|---|---|---|---|
| gameorder | int64 | 0 | 63,157 | 1..63157, non-decreasing in file order |
| game_id | object | 0 | 63,157 | `^\d{9}[A-Z]{3}$` on 100% of rows; treat as opaque (see §3.3) |
| lg_id | object | 0 | 2 | NBA 118,016 / ABA 8,298 |
| _iscopy | int64 | 0 | 2 | 0: 63,157 / 1: 63,157 — see §2.2 |
| year_id | int64 | 0 | 69 | season label; 1947 = 1946-47 |
| date_game | object | 0 | 12,426 | US m/d/Y |
| seasongame | int64 | 0 | 108 | team's nth game of season incl. playoffs; see §7 |
| is_playoffs | int64 | 0 | 2 | 0: 118,248 / 1: 8,066 (rows) |
| team_id | object | 0 | 104 | |
| fran_id | object | 0 | 53 | franchise/lineage label |
| pts | int64 | 0 | 139 | 0..186 |
| elo_i | float64 | 0 | 123,947 | 538 pre-game Elo |
| elo_n | float64 | 0 | 123,982 | 538 post-game Elo |
| win_equiv | float64 | 0 | 123,857 | 10.15..71.11 (538) |
| opp_id | object | 0 | 104 | |
| opp_fran | object | 0 | 53 | |
| opp_pts | int64 | 0 | 139 | |
| opp_elo_i | float64 | 0 | 123,947 | |
| opp_elo_n | float64 | 0 | 123,982 | |
| game_location | object | 0 | 3 | H 63,138 / A 63,138 / N 38 |
| game_result | object | 0 | 2 | W 63,157 / L 63,157 — **no ties in NBA data** |
| forecast | float64 | 0 | 125,039 | 0.020447..0.979553 |
| notes | object | 120,890 | 232 | 95.7% null; see §6 |

### 2.2 `_iscopy` semantics (empirical)

Every game appears exactly twice (rows-per-game_id distribution: `{2: 63157}`;
distinct game_id = 63,157 = rows/2). `_iscopy=0` marks the **original row, which
is the home-team row**: crosstab `_iscopy x game_location` = `_iscopy=0` rows are
H: 63,138, A: 0, N: 19; `_iscopy=1` rows are H: 0, A: 63,138, N: 19. For the 19
neutral-site games (location=N for both rows) the `_iscopy=0` row is a designated
row with no home meaning.

### 2.3 Mirror verification (both rows of each game, n=63,157)

| check | violations |
|---|---|
| pts(_iscopy=0) == opp_pts(_iscopy=1) and reverse | 0 |
| elo_i(_iscopy=0) == opp_elo_i(_iscopy=1) and reverse | 0 |
| team_id/opp_id, fran_id/opp_fran correctly swapped | 0 |
| location inverted (H/A) or NN | 0 |
| result inverted (W/L; pairs WL 39,311 / LW 23,846) | 0 |
| year_id, date, gameorder, is_playoffs equal within game | 0 |
| forecast complementarity max \|f_a + f_b − 1\| | 3.4e-08 (stored at 8 dp) |

**(team_id, game_id) duplicates: 0. Fully duplicated rows: 0.**

## 3. Chronology & coverage (check 3)

### 3.1 Global ordering
- min(date_game) = **1946-11-01**, max(date_game) = **2015-06-16**.
- Rows dated >= 2016: **0**. Rows dated on/after 2015-07-01: **0**.
- `gameorder` non-decreasing: True (1..63157). `date_game` non-decreasing across
  the file: True. No gameorder group spans >1 date.
- **The file is globally sorted chronologically; the last game is 2015 Finals G6
  (CLE 97-105 GSW, 2015-06-16, game_id 201506170CLE, gameorder 63157).**
- Season 2015 (2014-15) is COMPLETE in-file: 1,230 RS + 81 playoff games.

### 3.2 Per-season census vs era expectation
Expectation = (measured distinct teams per season) x (era schedule length)/2 +
approx playoff games for the era's round format (see audit_script.py `SCHED`).
Schedule table: 60 (1947), 48 (1948), 60 (1949), 66-72 (1950s), 75 (1960),
79 (1961), 80 (1962-66), 81 (1967), 82 (1968+, except 50 in 1999, 66 in 2012).
**Result: 0 of 69 seasons deviate more than 10% from expectation.**

Full table (year_id: teams, games, RS, PO, expected, dev%):

```
1947: 11t  350g (331RS+19PO)  exp 350  +0.0%   | 1948:  8t  215g (192+23)  exp 214  +0.5%
1949: 12t  380g (360+20)      exp 390  -2.6%   | 1950: 17t  593g (561+32)  exp 608  -2.5%
1951: 11t  380g (354+26)      exp 393  -3.3%   | 1952: 10t  355g (330+25)  exp 360  -1.4%
1953: 10t  374g (351+23)      exp 380  -1.6%   | 1954:  9t  347g (324+23)  exp 354  -2.0%
1955:  8t  309g (288+21)      exp 323  -4.3%   | 1956:  8t  311g (288+23)  exp 323  -3.7%
1957:  8t  307g (288+19)      exp 323  -5.0%   | 1958:  8t  309g (288+21)  exp 323  -4.3%
1959:  8t  310g (288+22)      exp 323  -4.0%   | 1960:  8t  325g (300+25)  exp 335  -3.0%
1961:  8t  341g (316+25)      exp 351  -2.8%   | 1962:  9t  389g (360+29)  exp 395  -1.5%
1963:  9t  389g (360+29)      exp 395  -1.5%   | 1964:  9t  387g (360+27)  exp 395  -2.0%
1965:  9t  386g (360+26)      exp 395  -2.3%   | 1966:  9t  387g (360+27)  exp 395  -2.0%
1967: 10t  436g (405+31)      exp 450  -3.1%   | 1968: 23t  994g (921+73)  exp 988  +0.6%  [NBA+ABA]
1969: 25t 1084g (1003+81)     exp 1070 +1.3%   | 1970: 25t 1116g (1036+80) exp 1070 +4.3%  [NBA+ABA]
1971: 28t 1240g (1159+81)     exp 1193 +3.9%   | 1972: 28t 1237g (1159+78) exp 1193 +3.7%  [NBA+ABA]
1973: 27t 1197g (1117+80)     exp 1152 +3.9%   | 1974: 27t 1197g (1117+80) exp 1152 +3.9%  [NBA+ABA]
1975: 28t 1245g (1158+87)     exp 1208 +3.1%   | 1976: 27t 1118g (1045+73) exp 1167 -4.2%  [NBA+ABA]
1977: 22t  955g (902+53)      exp 962  -0.7%   | 1978: 22t  953g (902+51)  exp 962  -0.9%
1979: 22t  955g (902+53)      exp 962  -0.7%   | 1980: 22t  950g (902+48)  exp 962  -1.2%
1981: 23t  996g (943+53)      exp 1003 -0.7%   | 1982: 23t  990g (943+47)  exp 1003 -1.3%
1983: 23t  986g (943+43)      exp 1003 -1.7%   | 1984: 23t 1022g (943+79)  exp 1013 +0.9%
1985: 23t 1011g (943+68)      exp 1028 -1.7%   | 1986: 23t 1011g (943+68)  exp 1028 -1.7%
1987: 23t 1014g (943+71)      exp 1028 -1.4%   | 1988: 23t 1023g (943+80)  exp 1028 -0.5%
1989: 25t 1087g (1025+62)     exp 1110 -2.1%   | 1990: 27t 1179g (1107+72) exp 1192 -1.1%
1991: 27t 1175g (1107+68)     exp 1192 -1.4%   | 1992: 27t 1180g (1107+73) exp 1192 -1.0%
1993: 27t 1183g (1107+76)     exp 1192 -0.8%   | 1994: 27t 1184g (1107+77) exp 1192 -0.7%
1995: 27t 1180g (1107+73)     exp 1192 -1.0%   | 1996: 29t 1257g (1189+68) exp 1274 -1.3%
1997: 29t 1261g (1189+72)     exp 1274 -1.0%   | 1998: 29t 1260g (1189+71) exp 1274 -1.1%
1999: 29t  791g (725+66)      exp 810  -2.3%  [lockout: 50-game schedule]
2000: 29t 1264g (1189+75)     exp 1274 -0.8%   | 2001: 29t 1260g (1189+71) exp 1274 -1.1%
2002: 29t 1260g (1189+71)     exp 1274 -1.1%   | 2003: 29t 1277g (1189+88) exp 1274 +0.2%
2004: 29t 1271g (1189+82)     exp 1274 -0.2%   | 2005: 30t 1314g (1230+84) exp 1315 -0.1%
2006: 30t 1319g (1230+89)     exp 1315 +0.3%   | 2007: 30t 1309g (1230+79) exp 1315 -0.5%
2008: 30t 1316g (1230+86)     exp 1315 +0.1%   | 2009: 30t 1315g (1230+85) exp 1315  0.0%
2010: 30t 1312g (1230+82)     exp 1315 -0.2%   | 2011: 30t 1311g (1230+81) exp 1315 -0.3%
2012: 30t 1074g ( 990+84)     exp 1075 -0.1%  [lockout: 66-game schedule]
2013: 30t 1314g (1229+85)     exp 1315 -0.1%  [1229 = 1 game cancelled, see A11]
2014: 30t 1319g (1230+89)     exp 1315 +0.3%   | 2015: 30t 1311g (1230+81) exp 1315 -0.3%
```

Structural notes (all explained, none are data errors):
- **1999**: 50-game lockout schedule (29t x 50/2 = 725 RS — exact).
- **2012**: 66-game lockout schedule (30t x 66/2 = 990 RS — exact).
- **2013**: RS = 1,229 (not 1,230): BOS and IND each show 81 RS games — the
  cancelled BOS@IND game of 2013-04-16 (never rescheduled). Real-world correct.
- **1947**: CHS and STB played 61 RS games in the 11-team BAA (odd team count).
- **1968-1976**: seasons are NBA+ABA combined (see lg_id split, §3.2a).

### 3.2a NBA/ABA split by season (games)
ABA rows exist for year_id 1968..1976 (462, 471, 502, 503, 503, 459, 459, 460,
330 games; total 4,149). No game_id has >1 lg_id. The NBA-only seasons
1947-1967 and the dual-league seasons 1968-1976 must be handled explicitly by
the protocol (see anomaly A4).

### 3.3 game_id anatomy (measured, for the record)
- Format `^\d{9}[A-Z]{3}$` on 100% of rows: `YYYYMMDD` + same-day sequence digit
  + 3-letter team code. The 9th char is `1` for exactly 6 games (the same-day
  double games listed in §5).
- date prefix != date_game for exactly **2 games** (4 rows), both +1 day:
  `200803080ATL` (protest completion actually played 3/7/2008) and
  `201506170CLE` (Finals G6, date_game 6/16/2015).
- Suffix = home team code on 62,160/63,138 H rows; the 978 exceptions (all
  1947-1962) use the franchise's *modern* code (e.g., PHW home games carry
  suffix `GSW`). 538 was inconsistent about historical vs modern codes.
- **Rule: treat game_id as an opaque key. Never parse the date prefix or suffix
  for identity/date logic** (anomaly A8).

## 4. Identity: franchises and continuity (check 4)

- 104 distinct team_id, 53 distinct fran_id.
- **0 team_ids map to >1 fran_id** (no id collisions between franchises).
- 25 fran_ids have >1 team_id (relocations/renames). No fran_id has a temporal
  gap that would imply two separate real franchises: the 3 detected anomalies
  (PTP missing 1969 -> was MNP; NOH missing 2006-07 -> was NOK; DLC missing
  1971 -> was TEX) are relocations/rebrands *within* the same lineage, verified
  contiguous at fran level.
- **Naming traps** (documented, must not be "fixed" by intuition):
  - fran `Thunder` = SEA (Seattle SuperSonics 1968-2008) + OKC. SEA rows carry
    fran_id "Thunder" retroactively.
  - fran `Wizards` = CHP/CHZ (Chicago Packers/Zephyrs) -> BAL -> CAP -> WSB
    (Bullets eras) -> WAS. No fran_id "Bullets" exists.
  - fran `Hornets` = CHA + CHO — this is the **Charlotte Bobcats** lineage
    (2004-14 Bobcats, renamed Hornets 2014).
  - fran `Pelicans` = CHH (Charlotte Hornets 1989-2002) + NOH + NOK (Katrina
    seasons in OKC) + NOP — the *original* Hornets lineage, retro-named
    Pelicans. **538 assigns official NBA history differently from the NBA's own
    2014 attribution; we follow the 538 on-court lineage** (anomaly A13).
- Every fran_id is a single connected on-court lineage over 1947-2015 ->
  **fran_id is adopted as the model's lineage key** (see DATASET_SCHEMA.md).

### 4.1 FRANCHISE CONTINUITY MAP (53 lineages, team_id [first-last season])

```
Baltimore:   BLB [1948-1954]                       Bombers:      STB [1947-1950]
Bucks:       MIL [1969-2015]                       Bulls:        CHI [1967-2015]
Capitols:    WSC [1947-1951]                       Cavaliers:    CLE [1971-2015]
Celtics:     BOS [1947-2015]
Clippers:    BUF [1971-1978] -> SDC [1979-1984] -> LAC [1985-2015]
Colonels:    KEN [1968-1976]          (ABA)
Condors:     PTP [1968-1970] -> MNP [1969] -> PTC [1971-1972]   (ABA; MNP overlaps)
Denver:      DNN [1950-1950]          (NBL-era; NOT the modern Nuggets lineage)
Falcons:     DTF [1947-1947]
Floridians:  MNM [1968] -> MMF [1969-1970] -> FLO [1971-1972]   (ABA)
Grizzlies:   VAN [1996-2001] -> MEM [2002-2015]
Hawks:       TRI [1950-1951] -> MLH [1952-1955] -> STL [1956-1968] -> ATL [1969-2015]
Heat:        MIA [1989-2015]
Hornets:     CHA [2005-2014] -> CHO [2015]          (= Bobcats lineage; see naming trap)
Huskies:     TRH [1947-1947]
Ironmen:     PIT [1947-1947]
Jazz:        NOJ [1975-1979] -> UTA [1980-2015]
Jets:        INJ [1949-1949]
Kings:       ROC [1949-1957] -> CIN [1958-1972] -> KCO [1973-1975] -> KCK [1976-1985] -> SAC [1986-2015]
Knicks:      NYK [1947-2015]
Lakers:      MNL [1949-1960] -> LAL [1961-2015]
Magic:       ORL [1990-2015]
Mavericks:   DAL [1981-2015]
Nets:        NJA [1968] -> NYA [1969-1976] -> NYN [1977] -> NJN [1978-2012] -> BRK [2013-2015]
Nuggets:     DNR [1968-1974] -> DNA [1975-1976] -> DEN [1977-2015]  (ABA->NBA; DNN 1950 is separate)
Olympians:   INO [1950-1953]
Packers:     AND [1950-1950]          (NBL-era)
Pacers:      INA [1968-1976] -> IND [1977-2015]  (ABA->NBA)
Pelicans:    CHH [1989-2002] -> NOH [2003-2013, minus 06-07] -> NOK [2006-2007] -> NOP [2014-2015]
Pistons:     FTW [1949-1957] -> DET [1958-2015]
Raptors:     TOR [1996-2015]
Rebels:      CLR [1947-1947]
Redskins:    SHE [1950-1950]
Rockets:     SDR [1968-1971] -> HOU [1972-2015]  (ABA->NBA)
Sails:       SDA [1973-1975] -> SDS [1976]       (ABA)
Sixers:      SYR [1950-1963] -> PHI [1964-2015]
Sounds:      NOB [1968-1970] -> MMP [1971-1972] -> MMT [1973-1974] -> MMS [1975]  (ABA)
Spirits:     HSM [1968-1969] -> CAR [1970-1974] -> SSL [1975-1976]  (ABA)
Spurs:       DLC [1968-1973, minus 1971] -> TEX [1971] -> SAA [1974-1976] -> SAS [1977-2015]  (ABA->NBA)
Squires:     OAK [1968-1969] -> WSA [1970] -> VIR [1971-1976]  (ABA)
Stags:       CHS [1947-1950]
Stars:       ANA [1968] -> LAS [1969-1970] -> UTS [1971-1976]  (ABA)
Steamrollers: PRO [1947-1949]
Suns:        PHO [1969-2015]
Thunder:     SEA [1968-2008] -> OKC [2009-2015]
Timberwolves: MIN [1990-2015]
Trailblazers: POR [1971-2015]
Warriors:    PHW [1947-1962] -> SFW [1963-1971] -> GSW [1972-2015]
Waterloo:    WAT [1950-1950]
Wizards:     CHP [1962] -> CHZ [1963] -> BAL [1964-1973] -> CAP [1974] -> WSB [1975-1997] -> WAS [1998-2015]
```

(Full team_id -> fran_id table is reproduced by `audit_script.py`; 104 rows,
each with first/last season and game count — kept in the script output rather
than duplicated here; the map above is the authoritative lineage view.)

## 5. Same-day pairs + games/day distribution (check 5)

- `(team_id, date_game)` appearing twice: **12 pairs, 0 duplicate games.**
  All are legitimate distinct game_ids (`...0XXX` / `...1XXX` seq digit):
  - **Protested-game completions** (5 pairs — remainder of an earlier protested
    game, replayed from the protest point, counted as its own game on the
    completion date): ATL/CHI 1970-02-08 (from 1969-11-06), ATL/MIA 2008-03-07
    (from 2007-12-19; explains the game_id/date mismatch of 200803080ATL),
    LAL/SAS 1983-04-13 (from 1982-11-30), NJN/PHI 1979-03-23 (from 1978-11-08),
    NYA/VIR 1976-01-24 (from 1976-01-07, at Norfolk VA).
  - **Genuine same-day doubleheader** (1 pair, no note): MLH vs BLB on
    1954-03-08 (64-54 and 65-54).
- Games per day: 12,426 distinct dates; mean 5.08, median 4, **max 15**
  (30-team era; 4/16/2014, 1/2/2009, 4/17/2013, 4/13/2011).

## 6. Neutral site + notes census (check 6)

- `game_location` domain is {H, A, N}. **N = 19 games (38 rows)**: Japan
  (Tokyo 1990, Yokohama 1992, Yokohama 1994, Tokyo 1996) and Mexico City 1997,
  all regular season, notes = "at <city> ...". Both rows carry location N; the
  `_iscopy=0` row is a designation with no venue meaning.
- `notes` non-empty on 5,424 rows (4.294%):
  - 5,346 rows (2,673 games): `at <city/state>` = the HOME team hosted at an
    alternate venue (very common pre-1963; e.g. Baltimore Armory, Hershey PA).
  - 11 games `Tiebreaker` (1948-1975), 11 games `Round Robin` (1954) — genuine
    counting games.
  - 10 games with malformed truncated note ` Edmundson Pavillion)` (SEA home
    games 1968-1987) — source-data cosmetic defect only.
  - 4 rows: famous own-goal scoring notes (Mikan 1949? per file 2 rows,
    Schayes 2, Wicks 2 — 3 games x 2 perspectives).
  - 8 rows: "Completion of protested game ..." (the 4 completion games above).
  - 1 game: `at Richmond VA; forfeit to VIR` (see §7).

## 7. Missing/duplicate/integrity (check 7)

- **Nulls: only `notes` (120,890 null). All 22 other columns: 0 nulls.**
- Duplicate (game_id, team_id): 0. Fully duplicated rows: 0.
- Games with both rows same location: 0. Same result: 0.
- pts mirror violations: 0. `(pts > opp_pts) != (result == W)`: **0 rows**.
  Rows with pts == opp_pts: 0 (no ties).
- pts range 0..186. Games > 190: 0. **pts == 0: exactly 1 game** — 1972-10-26
  DNR @ VIR 0-2, `notes = "at Richmond VA; forfeit to VIR"` (ABA forfeit; keep
  and flag — margin -2 is not basketball-representative).
- `seasongame` = team's nth game of the season **including playoffs**: range
  1..108; all 1,487 team-seasons start at exactly 1, increase by exactly 1 per
  game (0 violations), and max(seasongame) == that team's game count in 100% of
  team-seasons. Max 108 = BOS 2008 (82 RS + 26 playoff games).

## 8. Playoff structure (check 8)

- 8,066 playoff rows = **4,033 playoff games**; per-season range 19 (1947) ..
  89 (2006, 2014); no season <10 or >130. 1968-1976 seasons include both NBA
  and ABA playoffs. 2015: 81 playoff games (15 series, Finals ended G6).
- Sanity: best-of formats and round counts explain all variation; no season
  shows a structurally impossible count.

## 9. 538 Elo/forecast columns (cross-check ONLY — informs, does not replace, our Elo) (check 9)

- `elo_i`: 1091.6 .. 1853.1 (mean 1495.2). By era (min/max/mean):
  1947-50: 1125/1732/1414; 50s: 1269/1728/1520; 60s: 1092/1755/1451;
  70s: 1127/1757/1483; 80s: 1190/1816/1504; 90s: 1111/1853/1501;
  2000s: 1202/1782/1509; 2010-15: 1155/1814/1512. `elo_n`: 1085.8..1853.1.
- `forecast` in [0.020447, 0.979553]; game pairs satisfy |f_a + f_b − 1| max
  3.4e-08 (perfectly complementary at storage precision).
- **Season-boundary reversion**: factor = (elo_i, first game of season − 1500) /
  (elo_n, last game of previous season − 1500), n = 1,338 team-seasons with
  prior history (|denominator| > 5): **median 0.7542, p10 0.7161, p90 0.7887**;
  stable across decades (0.74-0.76). This is 538's ~0.75 reversion-to-mean at
  season start. (The naive estimate using pre-game elo_i of the final game
  gives 0.7278 — noisier because it omits the last game's update.)
- **Expansion cold start: a franchise's first-ever game has elo_i = 1300.0
  exactly (42 of 104 team_ids; e.g., TOR 1995-11-03, VAN 1995-11-03, CHA
  2004-11-04, CHH 1989, MIA 1989, ORL 1990). Relocated/renamed team_ids inherit
  the lineage rating (OKC 1353.5 from SEA; MEM 1391.0 from VAN; NOH 1541.0 from
  CHH). No clamping at 1300 in later seasons (VAN opens year 2 at 1294.7).**
- Usage boundary: elo_*/forecast/win_equiv are 538 computations over these same
  games. They may be used as a **baseline comparator / cross-check**, never as
  model input features (leakage of the label into features via 538's model).

## 10. COVID / bubble era (check 10)

Rows dated 2020-01-01..2021-12-31: **0**. Rows dated on/after 2015-07-01: **0**.
**NOT_APPLICABLE — the file ends 2015-06-16; the 2019-20 bubble season is not
in this dataset.** Any future extension to 2015+ requires a different source
(decision outside lane B).

---

## Anomaly / assumption register (for DATASET_SCHEMA.md and the protocol)

- **A1 Coverage end**: data ends 2015-06-16; seasons 2016+ absent. v1 universe
  = seasons 1947..2015 (year_id).
- **A2 Era breaks in game play**: 3-point line 1979-80 (year_id 1980); BAA->NBA
  (1949-50 merger with NBL; file labels everything NBA from 1947); shot clock
  1954-55; ABA coexistence 1968-1976; ABA->NBA influx 1977 (DEN, IND, NJN, SAS
  carry 538 lineage continuity). Win-prob features must be era-aware or the
  model must be able to absorb these shifts; v1 protocol should state a
  treatment (e.g., era feature or train-span choice).
- **A3 Dual-league seasons 1968-1976**: NBA+ABA games coexist. Recommendation:
  keep lg_id in the canonical table; default modeling universe = NBA-only, with
  ABA available behind the flag (protocol decision).
- **A4 ABA->NBA continuity**: 538 carries ABA lineage ratings into the NBA
  (e.g., DEN/IND/NJN/SAS 1977 start from ABA-era ratings, not 1300).
- **A5 Expansion cold start**: first-ever game at elo 1300.0 (538 convention);
  our own Elo must pick and document a cold start (mirror 1300.0 for
  comparability, or 1500 — model lane decision).
- **A6 Season-boundary reversion ~0.75 toward 1500** (measured median 0.7542) —
  prior for our own Elo design, not a replacement.
- **A7 Neutral/alternate venue**: only 19 true N games (international);
  additionally 2,673 "home" games were hosted at alternate venues (notes "at
  ..."). Home-court-advantage terms are approximations; no venue identity data.
- **A8 game_id is opaque**: date prefix wrong by +1 day on 2 games; suffix
  inconsistent (978 H rows 1947-1962 use modern franchise code, e.g. PHW->GSW).
- **A9 Same-day double games**: 6 games share a (team, date) with another game
  (5 protest completions + 1 doubleheader). As-of features must order strictly
  by (date, gameorder); a team's "previous game" is by that order, and the
  completion games count on their recorded date (538 convention).
- **A10 Forfeit**: 1 game (1972-10-26 DNR@VIR 0-2). Keep, flag `is_forfeit`;
  consider exclusion switch for margin-sensitive analyses.
- **A11 2013 season has 1,229 RS games** (BOS@IND 2013-04-16 cancelled, never
  played; BOS and IND show 81). Not an error; must not be "corrected".
- **A12 Lockout seasons**: 1999 (50 games/team) and 2012 (66 games/team).
  2012 is inside the frozen test window — document, do not drop.
- **A13 fran_id naming traps** (Thunder includes SEA; "Hornets"=Bobcats
  lineage; "Pelicans"=original Hornets lineage; no "Bullets" fran): fran_id is
  the lineage key; the NBA's official 2014 history attribution is NOT used.
- **A14 No ties, no OT flag**: game_result {W,L} only; overtime games are not
  distinguishable. Limits win-prob feature engineering (documented limitation).
- **A15 538 columns are cross-check-only** (see §9 usage boundary).
- **A16 seasongame includes playoffs**; max 108 (BOS 2008).
- **A17 BAA-era oddities**: 11-team 1947 season, CHS/STB 61 games; Tiebreaker
  (11) and Round Robin (11) games are genuine.
- **A18 notes field defects**: 10 truncated ` Edmundson Pavillion)` values —
  cosmetic only.

## Appendix A — reproduction

Primary script: `audit_script.py` (this dir). Run `python3 audit_script.py`.
It prints every number in this document. Environment: python3 3.13.4,
pandas 2.3.1, numpy; no network; the script writes nothing.

## Appendix B — follow-up queries (recorded commands)

Key follow-ups beyond audit_script.py (all pandas one-offs over the same CSV):

1. Same-day pair classification (§5): group rows by (team_id, date_game) with
   size>1; print full rows — identified 5 protest completions + 1 doubleheader.
2. notes categories (§6): `nt.str.startswith("at ")` split; value_counts of the
   remainder; contains("Tiebreaker" / "Round Robin" / "Edmundson") per-game.
3. seasongame consistency (§7): per (team_id, year_id): max(seasongame) vs
   nunique(game_id); diff == 0 for 1487/1487; diff of consecutive seasongame
   along (date, gameorder) == 1 for all steps.
4. Carryover (§9): per team-season, (elo_i at seasongame==1 − 1500) /
   (elo_n of last game of previous season − 1500), denominator |>5|; median
   overall, by era, by decade (script logic reproduced in Appendix A script's
   CHECK 9 block, elo_n variant: n=1338, median 0.7542).
5. Expansion anchors (§9): `df.groupby("team_id").first()` on elo_i; 42 teams
   at exactly 1300.0; OKC/MEM/NOH first-game values carried from lineage.
6. game_id anatomy (§3.3): regex `^\d{9}[A-Z]{3}$` match rate 126,314/126,314;
   9th-char value_counts {0: 126,302 rows, 1: 12 rows}; H rows suffix vs
   team_id mismatch = 978 (all 1947-1962, modern-code anachronism).
7. Result consistency (§7): `((pts > opp_pts) != (result == "W")).sum()` = 0.
8. Year alignment: date year ∈ {year_id−1, year_id} for 126,314/126,314 rows;
   months present: Oct..Jun only (no Jul-Sep rows).
9. Home win rate: H rows result==W fraction = 0.6225 (63,138 rows).

— End of audit. Schema design: DATASET_SCHEMA.md (same dir).
