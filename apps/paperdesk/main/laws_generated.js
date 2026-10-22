'use strict';
// GENERATED FILE — DO NOT EDIT BY HAND (PAPERDESK-FIXALL-NCAA-V1 W1.6).
// Source of truth: research/papertrade_exec/laws.py; regenerate with
//   python research/papertrade_exec/build_laws_js.py
// Values are the frozen gate constants; the JS gate mirrors consume them
// from here so Python and JS can never silently diverge.
module.exports = {
  "BATCH_LEAD_SECONDS": 22200,
  "DRAWDOWN_PAUSE": 0.1,
  "EV_OUTLIER_THRESHOLD": 1.0,
  "EV_THRESHOLD": 0.05,
  "FLAT_FEE_PRE_CUTOVER": 0.02,
  "OPEN_CAP_CENTS_V2": 50000,
  "OPEN_CAP_CENTS_V3": 50000,
  "PM_TAKER_FEE_RATE": 0.05,
  "SOCCER_LEAD_SECONDS": 21600,
  "STAKE_FRACTION_OF_EQUITY": 0.01,
  "STAKE_ROUNDING": "(equity_cents + 50) // 100  (1% of equity, half-up)"
};
