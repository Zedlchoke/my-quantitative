'use strict';
// P0 fix: every book-walk MUST use the CURRENT 1% equity stake computed
// from a fresh equity read under lock — never a hardcoded prior stake.
// Mirrors capital V3 via laws_generated (W1.6: ONE constant source):
// stake = (equity_cents + 50) // 100 cents (1%, half-up via +50 round).
// Equity is re-read from /api/state or ledger.
const LAWS = require('./laws_generated');
function currentStakeCents(equityCents) {
  if (typeof equityCents !== 'number' || equityCents < 100) return 0;
  return Math.floor((equityCents + 50) / 100);
}
module.exports = { currentStakeCents, LAWS };
