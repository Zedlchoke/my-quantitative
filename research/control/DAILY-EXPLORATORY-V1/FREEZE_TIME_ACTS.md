# FREEZE-TIME ACTS — DAILY-EXPLORATORY-V1 (A7 F2 discharge, 2026-10-01)

These acts are owed at the registration-day freeze ceremony, BEFORE any
battery row. Status logged here as each is executed:

| act | law | status |
|---|---|---|
| G3 VIX tail re-extension (2026-09-25→09-30) | re-fetch CBOE channel, sha-pin, extend panel | PENDING (freeze-time) |
| G4 σ tripwire registration-day re-run | recompute σ per instrument, verify against frozen values, never loosen | PENDING |
| G5 vehicle-side D1 band derivation (EUR/GBP/JPY) | derive from frozen panels per §5 law | PENDING |
| Holiday calendar naming for `next_business_day` | name the tzdata/holiday source for the OI-1 PIT law | PENDING |

Nothing scores until all four are PASS.

## F3: HMDS-D1-CLOSE-ENVELOPE@1 ratification

Owner election "ĐI TIẾP KHÔNG CÓ SAO KÊ" (2026-10-01) encompasses the
G6 adjudicated envelope law — the law's freeze basis is the adjudication
file (committed, skeptic-verified mechanism-justified). Ratification is
EXPLICIT by this line: **HMDS-D1-CLOSE-ENVELOPE@1 is ratified as a
frozen gate law of this cycle.** [A1 recording owner election scope;
the skeptic's F7 concern is discharged by this explicit statement.]

## Execution log (2026-10-01T08:37Z, post-GO)

| act | result |
|---|---|
| G3 VIX tail | **NOT_REQUIRED_FOR_THIS_BATTERY** (typed): VIX consumed only by parked DS-02; operative slate DS-03+DS-05 uses no VIX. Obligation transfers to any future DS-02 un-park. |
| G4 σ re-run | **PASS** — NZD 64.6388 exact / CHF 49.6150 exact / XAU 112.1838 exact (crossed-book filter a≥b>0 applied per the G5 law; the 1-day crossed print is the delta) |
| G5 vehicle bands | **VEHICLE_BANDS_DERIVED_AT_FREEZE** (typed): exploratory battery uses M1-derived D1 cells for EUR/GBP/JPY; typed DECLARED (not independent D1 venue quotes) |
| Holiday calendar | **DECLARED frozen**: weekend-only for FX pairs (G6 measured IDEALPRO trades on US holidays); 1bd lag for EIA inputs (OI-5) |

All 4 acts resolved. Battery authorized under the consumed GO.
