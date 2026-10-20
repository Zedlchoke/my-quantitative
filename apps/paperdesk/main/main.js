'use strict';
// PaperDesk — Electron main process. UI + lifecycle controller for
// SPORTS-PAPERTRADE-EXEC-V1 (paper money only; LiveExecution sealed).
//
// CLI modes (also work in the packaged .app):
//   --self-check-ledger P   print chain-verify JSON for P, exit (e2e/A7)
//   --sandbox               operate on the sandbox data plane (demo/e2e)
//   --data-root P           override data root
//   --worktree P            override runner worktree (cwd for child service)
//   --ui-evidence DIR       walk sections writing PNG evidence, then keep
//                           running (caller quits)
//   --auto-quit N           quit (real graceful-stop flow) after N seconds
const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const fs = require('fs');
const path = require('path');
const { parseLedger } = require('./ledger');
const { RunnerController } = require('./runner');
const { HealthStore, PolymarketProvider } = require('./market');
const { AIReviewEngine, deadlineFor } = require('./ai');
const { buildCandidates } = require('./candidates');
const { evaluateAIPaperAction, snapshotFromMatchView }
  = require('./paper_policy');
const { LIVE_EXECUTION_SEAL, PAPER_DECISION_OUTCOMES }
  = require('./seal');

const DEFAULT_DATA_ROOT
  = '/Users/hoangminhlong/.my-quantitative-data/sports-papertrade-exec-v1';
const DEFAULT_WORKTREE = '/Users/hoangminhlong/my-quantitative/.worktrees/'
  + 'sports-papertrade-exec-v1/integration';

let sandbox = false;
let dataRoot = DEFAULT_DATA_ROOT;
let worktreeDir = DEFAULT_WORKTREE;
let uiEvidenceDir = null;
let autoQuitAfter = null;
let autoYes = false;          // e2e: auto-confirm dialogs (default button)

// ---------------------------------------------------------------- arg parse --
(function parseArgs() {
  const a = process.argv;
  for (let i = 0; i < a.length; i++) {
    switch (a[i]) {
      case '--sandbox': sandbox = true; break;
      case '--data-root': dataRoot = a[++i]; break;
      case '--worktree': worktreeDir = a[++i]; break;
      case '--ui-evidence': uiEvidenceDir = a[++i]; break;
      case '--auto-quit': autoQuitAfter = Number(a[++i]); break;
      case '--yes': autoYes = true; break;
      case '--self-check-ledger': {
        const snap = parseLedger(a[++i]);
        const out = { path: a[i], rows: snap.rows.length,
                      sandbox: snap.isSandbox,
                      chain_ok: snap.chain.ok,
                      verified_rows: snap.chain.verified_rows,
                      errors: snap.chain.errors,
                      parse_error: snap.parseError };
        process.stdout.write(JSON.stringify(out) + '\n');
        app.exit(0);
        break;
      }
      default: break;
    }
  }
})();

if (!app.requestSingleInstanceLock()) {
  // single-instance guard for the APP (the runner has its own service.lock)
  // NOTE: app.exit() before 'ready' is unreliable in secondary instances —
  // use a hard process exit for the e2e path and a fallback timer otherwise.
  if (autoYes) {
    process.exit(3);
  }
  app.whenReady().then(() => {
    dialog.showMessageBoxSync({
      type: 'warning',
      message: 'PaperDesk is already running',
      detail: 'Only one PaperDesk instance may control the paper runner '
        + '(single-instance guard). Use the running app.',
    });
    app.exit(3);
  });
  setTimeout(() => process.exit(3), 5000);   // belt-and-braces
} else {
  boot();
}

function boot() {
  const runner = new RunnerController({ dataRoot, sandbox, worktreeDir });
  const health = new HealthStore();
  const pm = new PolymarketProvider(
    path.join(dataRoot, 'pm_ui_snapshots'));
  const ai = new AIReviewEngine(dataRoot);
  let ledger = parseLedger(
    sandbox ? path.join(dataRoot, 'sandbox/sandbox_ledger.jsonl')
      : path.join(dataRoot, 'ledger/paper_ledger.jsonl'));
  let win = null;
  let section = 'dashboard';
  function readPolicy() {
    try {
      return fs.readFileSync(
        path.join(app.getPath('userData'), 'window_close_policy'),
        'utf8').trim();
    } catch (e) { return 'ask'; }
  }
  function writePolicy(p) {
    try {
      fs.mkdirSync(app.getPath('userData'), { recursive: true });
      fs.writeFileSync(
        path.join(app.getPath('userData'), 'window_close_policy'), p);
    } catch (e) { /* best-effort */ }
  }
  let windowClosePolicy = readPolicy();
  let aiAutomation = 'Machinery TESTED (canonical candidate builder + '
    + 'rolling-window budget + anchor-law windows + idempotence, 43/43 '
    + 'seam); scheduler IDLE while mode is disabled-no-entitlement — no '
    + 'opinions are generated. GLM/Z.ai live: STOPPED by owner '
    + '(insufficient balance, HTTP 429 errCode 1113, 2026-10-20); live '
    + 'provider is now the OpenRouter free chain (ranked, fallback on '
    + '429/quota/5xx/timeout, ABSTAIN if all fail)';
  let ticker2 = null;
  let ticker3 = null;

  function ledgerPath() {
    return sandbox
      ? path.join(dataRoot, 'sandbox/sandbox_ledger.jsonl')
      : path.join(dataRoot, 'ledger/paper_ledger.jsonl');
  }

  function refreshLedger() {
    try {
      const st = fs.statSync(ledgerPath());
      if (!ledger || ledger.size !== st.size
          || ledger.mtime !== st.mtimeMs || !ledger.rows.length) {
        ledger = parseLedger(ledgerPath());
      }
    } catch (e) { ledger = parseLedger(ledgerPath()); }
  }

  function uiState() {
    return {
      section,
      sandbox,
      ledger: {
        chain: ledger.chain, rowsCount: ledger.rows.length,
        parseError: ledger.parseError, isSandbox: ledger.isSandbox,
        wallet: ledger.wallet, equity: ledger.equity,
        matches: ledger.matches,
        path: ledgerPath(),
      },
      runner: {
        state: runner.state.s, pid: runner.state.pid,
        source: runner.state.source,
        error: runner.state.error || null,
        lastAction: runner.lastAction,
        launchdOwned: runner.launchdOwned,
        paused: runner.decisionsPaused,
        heartbeat: runner.heartbeat,
      },
      health: {
        liveFetchError: health.liveFetchError,
        liveLastOK: health.liveLastOK,
        isStale: !health.liveLastOK
          || (Date.now() - health.liveLastOK) > 180000,
        live: health.liveState,
        pmProbe: health.pmProbe,
        pmJournalFailures: pm.journalFailures,
      },
      ai: {
        mode: ai.mode, entitlement: ai.entitlement,
        lastNote: ai.lastNote, opinions: ai.opinions.slice(0, 50),
        runtime: ai.mode === 'disabled-no-entitlement'
          ? 'NOT_RUN_AI_RUNTIME_ENTITLEMENT' : 'SHADOW · '
            + (ai.mode === 'shadow-mock' ? 'MOCK'
              : 'OpenRouter free chain'),
        automation: aiAutomation,
      },
      seal: { statement: LIVE_EXECUTION_SEAL.statement,
              activationConditions: LIVE_EXECUTION_SEAL
                .activationConditions },
      policy: windowClosePolicy,
      outcomes: PAPER_DECISION_OUTCOMES,
    };
  }

  let ticker = null;
  function broadcast() {
    if (win && !win.isDestroyed()) {
      try { win.webContents.send('state', uiState()); } catch (e) {}
    }
  }

  function createWindow() {
    win = new BrowserWindow({
      width: 1280, height: 820, minWidth: 1024, minHeight: 640,
      title: 'PaperDesk — SPORTS-PAPERTRADE-EXEC-V1 (PAPER)',
      show: false,
      webPreferences: {
        preload: path.join(__dirname, '..', 'renderer', 'preload.js'),
        contextIsolation: true, nodeIntegration: false,
        sandbox: true, spellcheck: false,
      },
    });
    win.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));
    win.webContents.on('console-message', (_e, level, message, line, src) => {
      if (level >= 2) {   // warn/error only
        runner.audit('RENDERER_CONSOLE', {
          level, line, src: String(src).split('/').pop(),
          message: String(message).slice(0, 300) });
      }
    });
    win.once('ready-to-show', () => win.show());
    win.on('close', e => {
      if (app.quitting) return;
      e.preventDefault();
      handleWindowClose();
    });
  }

  function ask(opts) {
    if (autoYes) return Promise.resolve({ response: opts.defaultId ?? 0 });
    return dialog.showMessageBox(win, opts);
  }

  // Window close ≠ quit: visible policy per owner law.
  async function handleWindowClose() {
    if (windowClosePolicy === 'pauseDecisions') {
      runner.setDecisionsPaused(true, 'window-close-policy');
      runner.audit('WINDOW_CLOSE', { policy: 'pause' });
      win.hide();
      return;
    }
    if (windowClosePolicy === 'keepRunning') {
      runner.audit('WINDOW_CLOSE', { policy: 'keep' });
      win.hide();
      return;
    }
    const r = await ask({
      type: 'question',
      message: 'Close window — what should the runner do?',
      detail: 'The app stays in the Dock. Quitting the app (⌘Q) always '
        + 'stops the paper runner gracefully.',
      buttons: ['Pause decisions', 'Keep deciding', 'Cancel'],
      defaultId: 0, cancelId: 2,
    });
    if (r.response === 0) {
      runner.setDecisionsPaused(true, 'window-close-ask');
      windowClosePolicy = 'pauseDecisions';
    } else if (r.response === 1) {
      windowClosePolicy = 'keepRunning';
    }
    writePolicy(windowClosePolicy);
    runner.audit('WINDOW_CLOSE', { policy: windowClosePolicy });
    if (r.response !== 2) win.hide();
  }

  app.on('second-instance', () => {
    if (win) { if (win.isMinimized()) win.restore(); win.show();
                win.focus(); }
  });

  // QUIT LAW: ⌘Q / Quit = ngừng paper — but FAIL-CLOSED: a stop that cannot
  // be verified complete (runner alive, identity lost, bootout failed, lock
  // still held) keeps the app OPEN with a visible error; half-stopped is
  // worse than running.
  app.on('before-quit', e => {
    if (app.quitting) return;
    app.quitting = true;
    e.preventDefault();
    (async () => {
      const r = await ask({
        type: 'question',
        message: 'Quit PaperDesk and stop the paper runner?',
        detail: 'Quit sends a graceful stop: no new forecast/quote/decision '
          + 'will run. Open bets stay OPEN in the ledger. Windows missed '
          + 'entirely while stopped are never backfilled — the cadence only '
          + 'looks at today..+2, and a startup reconciliation journals any '
          + 'in-scope missed window as an incident.',
        buttons: ['Quit & stop paper', 'Cancel'],
        defaultId: 0, cancelId: 1,
      });
      if (r.response !== 0) { app.quitting = false; return; }
      for (const t of [ticker, ticker2, ticker3]) {
        if (t) clearInterval(t);
      }
      const clean = await runner.gracefulStopRunner('app-quit');
      const stillHeld = runner.flockHeld(runner.serviceLockPath);
      if (!clean || stillHeld) {
        app.quitting = false;
        runner.audit('QUIT_BLOCKED',
          { clean, still_held: stillHeld });
        dialog.showErrorBox('Quit blocked — paper runner NOT safely stopped',
          'The graceful stop did not fully complete (clean=' + clean
          + ', service.lock held=' + stillHeld + ').\n\n'
          + 'PaperDesk stays open. Check System Health and the controller '
          + 'journal, then try Quit again.');
        return;
      }
      app.exit(0);
    })();
  });

  app.on('window-all-closed', () => { /* stay in Dock; no quit */ });
  app.on('activate', () => { if (win) win.show(); });

  // ----------------------------------------------------------------- IPC --
  ipcMain.handle('runner:start', async () => { await runner.startRunner(); });
  ipcMain.handle('runner:pause', (_e, paused, reason) =>
    runner.setDecisionsPaused(!!paused, String(reason || 'ipc')));
  ipcMain.handle('runner:stop', async () =>
    runner.gracefulStopRunner('manual-toolbar'));
  ipcMain.handle('runner:takeover', async () =>
    runner.takeoverFromLaunchd());
  ipcMain.handle('section:set', (_e, s) => { section = s; });
  ipcMain.handle('policy:set', (_e, p) => {
    windowClosePolicy = p; writePolicy(p); });
  ipcMain.handle('ai:setMode', (_e, m) => ai.setMode(m));
  // Attach the frozen-gate advisory evaluation to a finished opinion and
  // persist it in the AI sidecar (NEVER the ledger). Reads ledger snapshot
  // numbers only; the AI's own numbers carry no authority.
  function evaluateAndPersist(op) {
    try {
      const m = (ledger.matches || [])
        .find(x => x.matchId === op.matchID);
      const snap = snapshotFromMatchView(m, ledger.wallet);
      op.policyEvaluation = evaluateAIPaperAction(
        { opinion: op, fixture: snap });
      ai.store.save(op);
      ai.opinions = ai.store.list();
    } catch (e) {
      runner.audit('POLICY_EVAL_FAILED',
        { match: op.matchID, error: String(e).slice(0, 160) });
    }
  }
  ipcMain.handle('ai:run', async (_e, match) => {
    const op = await ai.runReview(match);
    evaluateAndPersist(op);
    broadcast();
    return op;
  });
  ipcMain.handle('ai:refreshEntitlement', () => ai.refreshEntitlement());
  ipcMain.handle('pm:probe', async () => health.probePolymarket());
  ipcMain.handle('pm:events', async () => pm.fetchEventsForDisplay());

  app.whenReady().then(async () => {
    // journal FIRST: any later failure must still leave a trace
    runner.audit('BOOT', { sandbox, dataRoot });
    // auto-quit registration must not depend on window creation succeeding
    if (autoQuitAfter != null) {
      setTimeout(() => app.quit(), autoQuitAfter * 1000);
    }
    process.on('uncaughtException', e =>
      runner.audit('UNCAUGHT_EXCEPTION', { error: String(e) }));
    process.on('unhandledRejection', e =>
      runner.audit('UNHANDLED_REJECTION', { error: String(e) }));
    try {
      Menu.setApplicationMenu(Menu.buildFromTemplate([
        { label: 'PaperDesk', submenu: [
          { role: 'about' },
          { type: 'separator' },
          { role: 'hide' }, { role: 'quit' }] },
        { label: 'Edit', submenu: [
          { role: 'undo' }, { role: 'redo' }, { type: 'separator' },
          { role: 'cut' }, { role: 'copy' }, { role: 'paste' },
          { role: 'selectAll' }] },
        { label: 'View', submenu: [
          { role: 'reload' }, { role: 'toggleDevTools' },
          { type: 'separator' },
          { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' },
          { type: 'separator' }, { role: 'togglefullscreen' }] },
        { label: 'Window', submenu: [
          { role: 'minimize' }, { role: 'zoom' }, { role: 'close' }] },
      ]));
      createWindow();
    } catch (e) {
      runner.audit('WINDOW_FAILED', { error: String(e) });
      dialog.showErrorBox('PaperDesk failed to open its window', String(e));
    }
    await runner.establish();
    refreshLedger();
    broadcast();
    ticker = setInterval(() => {
      runner.pollOnce();          // re-measure runner state (heartbeat/pid),
                                  // not just the ledger file — keeps the UI's
                                  // heartbeat age/tick_count fresh (audit fix)
      refreshLedger();
      broadcast();
    }, 2000);
    // AI auto-scheduler (P0 fix): every 30 s, gather candidate fixtures
    // (no decision row yet, kickoff in the future — from the ledger and the
    // runner's upcoming plan) and run due pre-anchor reviews. Idempotent per
    // (match, deadline); disabled mode records nothing.
    let aiSchedBusy = false;
    setInterval(() => {
      if (aiSchedBusy || ai.mode === 'disabled-no-entitlement') return;
      aiSchedBusy = true;
      try {
        const upcoming = (health.liveState
          && health.liveState.upcoming) || [];
        // CANONICAL-ID candidate building (round-3): plan entries without a
        // canonical match_id are skipped; no synthetic ids; a fixture in
        // both ledger and plan is ONE candidate; plan anchor_utc is the
        // authoritative deadline. See main/candidates.js (unit-tested).
        const built = buildCandidates({
          ledgerMatches: ledger.matches || [], upcoming,
        });
        if (built.skipped.length) {
          runner.audit('AI_SCHED_SKIPPED', { skipped: built.skipped });
        }
        const candidates = built.candidates;
        ai.maybeAutoReview(candidates, pm)
          .then(res => {
            if (res.ran && res.ran.length) {
              for (const r of res.ran) {
                const op = ai.opinions.find(
                  o => o.matchID === r.matchId
                    && o.opinionID === (r.opinionID || o.opinionID));
                const latest = ai.opinions.find(o => o.matchID === r.matchId);
                if (latest) evaluateAndPersist(latest);
              }
              runner.audit('AI_AUTO_REVIEW', { ran: res.ran });
              broadcast();
            }
          })
          .catch(e => runner.audit('AI_AUTO_REVIEW_FAILED',
                                   { error: String(e).slice(0, 200) }));
      } finally { aiSchedBusy = false; }
    }, 30000);
    ticker2 = setInterval(() => {
      health.fetchState(runner.heartbeat ? runner.heartbeat.port : null)
        .then(broadcast)
        .catch(e => runner.audit('POLL_FAILED', { error: String(e) }));
    }, 4000);
    ticker3 = setInterval(() => health.probePolymarket().then(broadcast)
      .catch(() => {}), 60000);
    health.probePolymarket().then(broadcast).catch(() => {});

    if (uiEvidenceDir) {
      setTimeout(() => runEvidenceTour(uiEvidenceDir), 5000);
    }
  });

  // In-process UI evidence: real window renders per section (no TCC needed).
  async function runEvidenceTour(dir) {
    const sections = ['dashboard', 'matches', 'opportunities', 'health',
                      'ai', 'laws'];
    try { fs.mkdirSync(dir, { recursive: true }); } catch (e) {}
    for (const s of sections) {
      section = s;
      if (win) win.webContents.send('state', uiState());
      await new Promise(r => setTimeout(r, 1700));
      try {
        const img = await win.webContents.capturePage();
        fs.writeFileSync(path.join(dir, `paperdesk_section_${s}.png`),
                         img.toPNG());
      } catch (e) { /* recorded by absence */ }
    }
    runner.setDecisionsPaused(true, 'ui-evidence');
    await new Promise(r => setTimeout(r, 800));
    try {
      const img = await win.webContents.capturePage();
      fs.writeFileSync(path.join(dir, 'paperdesk_state_paused.png'),
                       img.toPNG());
    } catch (e) {}
    runner.setDecisionsPaused(false, 'ui-evidence');
    runner.audit('UI_EVIDENCE_TOUR', { dir });
    section = 'dashboard';
  }
}
