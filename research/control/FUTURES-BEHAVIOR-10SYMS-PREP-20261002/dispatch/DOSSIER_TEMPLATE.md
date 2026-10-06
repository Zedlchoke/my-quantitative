# DOSSIER_TEMPLATE — {SYM} (replace braces; keep every heading; NOT_RUN is a valid answer)

Header: symbol, exchange, generated_utc, author lane id, inputs (framework file
sha256 from owner_framework/SHA256SUMS.txt + FINAL_REPORT.md).

## 1. Mechanics
Underlying exposure; hedgers/speculators/MMs/arbitrageurs; tick/multiplier/quote
convention (verify against S1/costs artifacts, do NOT assume); exchange sessions
+ DST handling; holidays; delivery/first-notice/expiry/price limits; listed
months & liquid maturities; liquidity migration front→next (OBSERVED from raw
volume if possible); PIT contract-selection + roll rule (use the data lane's
declared rule as baseline; note alternatives).

## 2. Causal driver map
Table per driver: source → mechanism → predicted sign/horizon → regime
dependency → confounders → falsification test → PIT data source (PRIMARY
official + access date). Cover the master framework's taxonomy buckets relevant
to {SYM}. Mark each driver's evidence class FACT/OBSERVED/POSTULATED/NOT_RUN.

## 3. Behavior (measured where legal)
Session / volatility / trend / event / curve / seasonality behavior. For every
statement: FACT(sourced) / OBSERVED(script+window) / POSTULATED / NOT_RUN.
Measure descriptives on the legal raw data if sufficient (strict past/rolling
windows for any threshold; ex-post labels for description only). Do NOT force
intraday numbers where the intraday window is ~10 months — say so and mark
NOT_RUN. Continuous-adjustment only as causal construction, description only.

## 4. Event calendar
Scheduled events relevant to {SYM}: actual release time UTC + exchange tz;
effective vs available vs retrieved; vintage/revision/consensus PIT notes.
Weather (NG): forecast vintages, never realized weather. CoT: release ≠
position date. Revised macro/ETF/earnings timing must be evidenced, not assumed.

## 5. Hypotheses (3–5, ranked by testability × causal plausibility — NOT by PnL)
Per hypothesis, full template: observable PIT condition → predicted move/horizon
→ economic mechanism → strongest/weakest regime; entry/exit/TP/SL/time/exit
rules explicit; direction; universe/roll; sizing; cost model; invalidation;
counter-hypothesis; failure conditions; data requirements/floors/budget.
PARAM-GAP where a rule cannot be specified without data we don't have — never
invent. Note any reuse of corpus-1200 ideas (line/ID) and flag FX→futures
transfer as hypothesis with basis/roll/cost differences, never "already valid".

## 6. Missing data table
Columns: need / have / source / period / schema / PIT properties / license /
cost / blocker / next action. Prioritize top-3 causal drivers; do not demand the
full wishlist as a condition for this dossier.

## 7. Framework coverage
List each question from owner_framework/00_MASTER_FRAMEWORK.md §1 (10 questions)
and the symbol framework's own checklist → answer + evidence class, or NOT_RUN.
