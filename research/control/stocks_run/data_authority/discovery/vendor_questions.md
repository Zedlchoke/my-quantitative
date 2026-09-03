# Vendor questions — close before any purchase decision

Concise questions whose answers would upgrade `UNKNOWN_NOT_RUN` /
`CONTACT_REQUIRED` fields in the coverage matrix. Ask vendors in writing;
record answers as evidence paths in `provider_evaluation_template.json`.

## To Norgate Data (before choosing Platinum vs Diamond)

- VQ-N1. Exact current USD price of the 12-month **US Platinum** subscription
  (the public calculator is dynamic; our snapshot only pinned Diamond at
  USD 787.50/12mo)?
- VQ-N2. Are historical index-constituent records **effective-dated only**, or
  do you also record the **announcement date** of each add/delete?
- VQ-N3. What is your formal **revision and correction policy** — are delivered
  historical files ever restated, and how are subscribers notified (R14/R19)?
- VQ-N4. Does the license permit **local research storage** and derived
  artifacts for a single individual researcher, including storage in Vietnam?
  May checksums/manifests (not raw data) be committed to a private repository?
- VQ-N5. Do you accept payment via international card or PayPal, or only the
  bank rails shown (USD ACH/wire, EUR SEPA, GBP wire)? Any country exclusions?
- VQ-N6. Provide sample delisted + constituent files (e.g., a 2018 delisting
  and the S&P 500 add/delete list for one rebalance) for ingestion trials.

## To Massive (ex-Polygon)

- VQ-M1. What is the maturity plan for the **experimental** ticker-events
  endpoint, and does it cover delisted symbols' full event timelines (R03)?
- VQ-M2. Are delisted tickers' full **price history** retained and served at
  the Advanced tier, and from when? Any survivorship caveats (R04/R07)?
- VQ-M3. Written terms on **local storage, flat-file export, and derived
  artifacts** for individual ("non-pro") researchers (R18).
- VQ-M4. Reference-data **revision/vintage policy**: can a subscriber pin a
  dated snapshot of dividends/splits/events so a scored window is never
  silently restated (R14)?
- VQ-M5. Are VN-issued cards accepted for self-service signup?

## To Sharadar / Nasdaq Data Link

- VQ-S1. Current SEP individual price and any per-API-call economics.
- VQ-S2. Evidence behind "point-in-time ready": sample as-of replays vs
  restatements (R01/R14).
- VQ-S3. Delisting completeness statement + sample of a 2018-era delisting.
- VQ-S4. Local bulk-storage rights under NDL individual terms (R18).

## To S3 Partners / FIS Astec / S&P Global MI (institutional borrow — F2)

- VQ-B1. Do you license to **individual researchers / small entities**? If
  entity required, what minimum size? (R18 gate for the owner)
- VQ-B2. **Historical depth** of daily borrow fee, utilization, and availability
  — how far back, at what granularity (R11/R12/R16)?
- VQ-B3. Are **recalls** events and **accrual conventions** (basis 360/365,
  fee accrual on holiday/weekend) documented and delivered as data? (F2 pin)
- VQ-B4. Minimum contract size and typical entry tier pricing (R18).
- VQ-B5. Vietnam-based individual/entity eligibility and payment.
- VQ-B6. Sample extract (one symbol, one month) for ingestion trials.

## To S&P Dow Jones Indices (R06 authority)

- VQ-I1. Is there a machine-readable archive of index-change announcements
  (announcement + effective dates) beyond press-release PDFs, and its depth?
- VQ-I2. License terms for curating a **local research archive** of official
  announcement texts (short excerpts vs full storage).
- VQ-I3. Commercial index-alert feed: pricing and individual eligibility.

## To CRSP/WRDS (reference standard)

- VQ-C1. Individual (non-university) access routes, if any.
- VQ-C2. Whether a university affiliation (if the owner obtains one) permits
  **commercial research** use of CRSP data.
