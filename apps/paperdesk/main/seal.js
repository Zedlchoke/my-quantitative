'use strict';
// EXECUTION SEAMS (owner-required architecture).
//
//   MarketDataProvider : read-only Gamma/CLOB (market.js — implemented).
//   PaperExecution     : the ONLY execution reality = the pinned runner
//                        process (ops_service -> execute.py -> pinned core).
//                        This app never appends to the ledger and never
//                        decides; the runner's decision outcome space is
//                        exposed purely as display metadata.
//   LiveExecution      : SEALED. Frozen, no order endpoint string, no auth
//                        header, no signing, no credential path anywhere in
//                        this app. See PAPERDESK_DECISION_PACKET_2026-10-19.

const PAPER_DECISION_OUTCOMES = Object.freeze([
  'BET_PAPER', 'NO_EDGE', 'NO_QUOTE', 'NO_FORECAST', 'STALE_PRICE',
  'CROSSWALK_MISS', 'RESOURCE_CONFLICT', 'QUOTA_SKIP', 'CANCELLED',
  'BLOCKED_OPEN_EXPOSURE', 'BLOCKED_DRAWDOWN_PAUSE', 'BLOCKED_NO_GO',
  'BLOCKED_DUPLICATE_SELECTION', 'PIT_VIOLATION_REFUSED', 'QUOTE_ANOMALY',
  'BLOCKED_INSUFFICIENT_EQUITY', 'NOT_RUN',
]);

const LIVE_EXECUTION_SEAL = Object.freeze({
  sealed: true,
  statement: 'LiveExecution: SEALED (no order path, no credentials, '
    + 'no endpoints).',
  activationConditions: Object.freeze([
    '1. separate owner-authorized cycle with its own registered GO phrase '
      + 'for live trading (NOT registered; the existing cutover phrase '
      + 'covers DATA cutover for the paper pipeline only)',
    '2. dedicated delegation gateway with external key custody, endpoint '
      + 'allow-list, per-order human confirmation',
    '3. independent A7 prelaunch audit of that gateway',
    '4. owner GO typed verbatim at that cycle\'s own gate (P-8)',
  ]),
  submit() {
    // The ONLY method, and it refuses. There is no network code, no order
    // payload type, no venue endpoint constant in this application.
    throw new Error('SEALED: LiveExecution has no implementation in '
      + 'PaperDesk. Live trading requires a separate authorized cycle, a '
      + 'delegation gateway, and an owner GO — see '
      + 'AMENDMENT_MACOS_APP_UI_V1 §2.');
  },
});

module.exports = { PAPER_DECISION_OUTCOMES, LIVE_EXECUTION_SEAL };
