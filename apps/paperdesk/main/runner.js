'use strict';
// Lifecycle controller for EXACTLY ONE paper runner (ops_service).
// Invariants (AMENDMENT_MACOS_APP_UI_V1): attach-before-spawn; never spawn
// into a held service.lock; Quit => graceful SIGTERM (SERVICE_STOP journaled,
// ledger untouched, open bets stay OPEN); pause flag gates NEW decisions only;
// launchd KeepAlive is booted out on takeover/quit (no auto-run at login).
// NO decision law lives here — the app only chooses WHEN.
const { spawn, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const https = require('https');

const PYTHON = '/Users/hoangminhlong/my-quantitative/.venv/bin/python';
const LAUNCHD_LABEL = 'com.myquant.sptexec.ops';

function nowZ() { return new Date().toISOString().replace(/\.\d+Z$/, 'Z'); }

class RunnerController {
  constructor({ dataRoot, sandbox, worktreeDir, auditDir }) {
    this.dataRoot = dataRoot;
    this.sandbox = sandbox;
    this.worktreeDir = worktreeDir;
    this.opsDir = path.join(dataRoot, sandbox ? 'sandbox/ops' : 'ops');
    this.controlDir = path.join(this.opsDir, 'control');
    this.heartbeatPath = path.join(this.opsDir, 'state', 'heartbeat.json');
    this.serviceLockPath = path.join(this.opsDir, 'service.lock');
    this.pauseFlagPath =
      path.join(this.controlDir, 'pause_decisions.flag');
    this.controllerLogPath =
      path.join(this.controlDir, 'controller_log.jsonl');
    this.child = null;
    this.state = { s: 'probing', pid: null, source: null };
    this.heartbeat = null;
    this.launchdOwned = false;
    this.lastAction = '';
  }

  ensureDirs() {
    fs.mkdirSync(this.controlDir, { recursive: true });
  }

  audit(event, detail) {
    this.ensureDirs();
    const row = { ts_utc: nowZ(), event,
                  detail: detail || {},
                  runner_pid: this.heartbeat ? this.heartbeat.pid : null };
    try {
      fs.appendFileSync(this.controllerLogPath,
        JSON.stringify(row) + '\n');
    } catch (e) { /* audit is best-effort; never blocks control */ }
  }

  // ------------------------------------------------------------ probing --
  readHeartbeat() {
    try {
      const hb = JSON.parse(fs.readFileSync(this.heartbeatPath, 'utf8'));
      const age = hb.ts_utc
        ? (Date.now() - Date.parse(hb.ts_utc.replace('Z', 'Z'))) / 1000 : null;
      return { pid: hb.pid || null, tsUTC: hb.ts_utc || null,
               ageSeconds: age, isFresh: age != null && age < 180,
               paused: !!hb.decisions_paused, sandbox: !!hb.sandbox,
               port: hb.port || null, tickCount: hb.tick_count || null,
               lastCadence: hb.last_cadence_result || null };
    } catch (e) { return null; }
  }

  pidAlive(pid) {
    try { process.kill(pid, 0); return true; } catch (e) { return false; }
  }

  pidIsOpsService(pid) {
    const r = spawnSync('/bin/ps', ['-p', String(pid), '-o', 'command='],
                        { encoding: 'utf8' });
    return r.status === 0 && String(r.stdout).includes('ops_service');
  }

  flockHeld(p) {
    this.ensureDirs();
    const r = spawnSync(PYTHON,
      [path.join(__dirname, '..', 'helpers', 'opslock.py'), 'probe', p],
      { encoding: 'utf8', timeout: 10000 });
    return String(r.stdout).trim() === 'HELD';
  }

  launchdState() {
    if (this.sandbox) return { loaded: false, pid: null };
    const r = spawnSync('/bin/launchctl',
      ['print', `gui/${process.getuid()}/${LAUNCHD_LABEL}`],
      { encoding: 'utf8', timeout: 10000 });
    if (r.status !== 0) return { loaded: false, pid: null };
    let pid = null;
    const m = String(r.stdout).match(/^\s*pid\s*=\s*(\d+)/m);
    if (m) pid = Number(m[1]);
    return { loaded: true, pid };
  }

  // ---------------------------------------------------------- lifecycle --
  pollOnce() {
    this.heartbeat = this.readHeartbeat();
    const ld = this.launchdState();
    this.launchdOwned = ld.loaded;
    if (this.state.s === 'stopping' || this.state.s === 'starting') return;
    const hb = this.heartbeat;
    if (hb && hb.pid && hb.isFresh && this.pidAlive(hb.pid)
        && this.pidIsOpsService(hb.pid)) {
      const source = (this.child && this.child.pid === hb.pid)
        ? 'child' : (ld.loaded ? 'launchd' : 'external');
      if (this.state.s !== 'attached' || this.state.pid !== hb.pid
          || this.state.source !== source) {
        this.state = { s: 'attached', pid: hb.pid, source };
        this.audit('ATTACH', { pid: hb.pid, source });
      }
    } else if (this.child && this.child.exitCode === null) {
      // child up, heartbeat not ready yet
    } else if (this.state.s === 'attached' && hb && hb.pid
               && !this.pidAlive(hb.pid)) {
      this.state = { s: 'detached', pid: null, source: null };
      this.audit('RUNNER_GONE', { pid: hb.pid });
    } else if (this.state.s === 'probing') {
      this.state = { s: 'detached', pid: null, source: null };
    }
  }

  async establish() {
    this.audit('APP_LAUNCH', { sandbox: this.sandbox });
    this.pollOnce();
    if (this.state.s !== 'attached') await this.startRunner();
  }

  startRunner() {
    return new Promise(resolve => {
      this.pollOnce();
      if (this.state.s === 'attached') {
        this.lastAction = 'Connected to running paper runner';
        return resolve(true);
      }
      if (this.flockHeld(this.serviceLockPath)) {
        this.lastAction = 'service.lock held but runner not healthy — '
          + 'attaching probe only';
        this.audit('SPAWN_REFUSED_LOCK_HELD', {});
        return resolve(false);
      }
      if (this.launchdOwned) {
        this.lastAction = 'Runner is launchd-managed — take over first';
        return resolve(false);
      }
      this.state = { s: 'starting', pid: null, source: null };
      this.lastAction = 'Starting paper runner…';
      const args = ['-m', 'research.papertrade_exec.ops_service',
                    '--data-root', this.dataRoot];
      if (this.sandbox) {
        // sandbox: no dashboard port (the REAL service owns 8791) and no
        // need for the live page in lifecycle tests — heartbeat + journals
        // carry all state the app reads.
        args.push('--sandbox', '--no-serve');
      }
      const child = spawn(PYTHON, args,
        { cwd: this.worktreeDir, stdio: ['ignore', 'pipe', 'pipe'] });
      let out = '';
      child.stdout.on('data', d => { out += d; });
      child.stderr.on('data', d => { out += d; });
      this.child = child;
      this.audit('SPAWN_CHILD', { pid: child.pid });
      child.on('exit', (code) => {
        this.audit('CHILD_EXIT', { code, tail: out.slice(-400) });
        if (this.child === child) {
          this.child = null;
          if (code === 3) this.lastAction =
            'Another supervisor already holds the lock';
          this.pollOnce();
        }
      });
      // wait for heartbeat ≤15s
      const t0 = Date.now();
      const tick = () => {
        const hb = this.readHeartbeat();
        if (hb && hb.pid === child.pid && hb.isFresh) {
          this.state = { s: 'attached', pid: child.pid, source: 'child' };
          this.lastAction = `Paper runner started (pid ${child.pid})`;
          this.audit('CHILD_READY', { pid: child.pid });
          return resolve(true);
        }
        if (child.exitCode !== null) {
          this.state = { s: 'failed', pid: null, source: null,
                         error: `runner exited with code ${child.exitCode}` };
          return resolve(false);
        }
        if (Date.now() - t0 > 15000) {
          this.state = { s: 'failed', pid: null, source: null,
                         error: 'heartbeat never appeared' };
          return resolve(false);
        }
        setTimeout(tick, 300);
      };
      setTimeout(tick, 300);
    });
  }

  // ------------------------------------------------------- pause/resume --
  setDecisionsPaused(paused, reason) {
    this.ensureDirs();
    if (paused) {
      fs.writeFileSync(this.pauseFlagPath, JSON.stringify({
        by: 'PaperDesk.app', at_utc: nowZ(), reason }), {});
      this.audit('PAUSE_ON', { reason });
    } else {
      try { fs.unlinkSync(this.pauseFlagPath); } catch (e) {}
      this.audit('PAUSE_OFF', { reason });
    }
    this.heartbeat = this.readHeartbeat();
  }

  get decisionsPaused() {
    try { return fs.existsSync(this.pauseFlagPath); } catch (e) {
      return false;
    }
  }

  // --------------------------------------------------------- graceful stop --
  sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  async gracefulStopRunner(reason) {
    this.pollOnce();
    if (this.state.s !== 'attached') {
      this.lastAction = 'No runner to stop';
      return true;
    }
    const { pid, source } = this.state;
    this.state = { s: 'stopping', pid, source };
    this.lastAction = 'Stopping paper runner gracefully…';
    this.audit('GRACEFUL_STOP_BEGIN', { pid, source, reason });
    if (source === 'launchd') {
      this.bootoutLaunchd();
      this.writeTakeoverRecord('quit');
    }
    const wasChild = this.child && this.child.pid === pid;
    this.child = null;
    try { process.kill(pid, 'SIGTERM'); } catch (e) {}
    const deadline = Date.now() + 8000;
    while (Date.now() < deadline && this.pidAlive(pid)) await this.sleep(250);
    const clean = !this.pidAlive(pid);
    if (!clean) {
      try { process.kill(pid, 'SIGKILL'); } catch (e) {}
      this.audit('GRACEFUL_STOP_FORCED_KILL', { pid });
    }
    const flDeadline = Date.now() + 3000;
    while (Date.now() < flDeadline && this.flockHeld(this.serviceLockPath)) {
      await this.sleep(200);
    }
    this.state = { s: 'stopped', pid: null, source: null };
    this.lastAction = clean
      ? 'Paper runner stopped gracefully (SERVICE_STOP journaled)'
      : 'Paper runner force-killed after timeout';
    this.audit('GRACEFUL_STOP_END', { pid, clean });
    this.heartbeat = this.readHeartbeat();
    return clean;
  }

  async takeoverFromLaunchd() {
    if (!this.launchdOwned) return false;
    const oldPID = this.heartbeat ? this.heartbeat.pid : null;
    this.audit('TAKEOVER_LAUNCHD_BEGIN', { pid: oldPID });
    this.bootoutLaunchd();
    if (oldPID) {
      const deadline = Date.now() + 8000;
      while (Date.now() < deadline && this.pidAlive(oldPID)) {
        await this.sleep(250);
      }
    }
    this.writeTakeoverRecord('app-takeover');
    this.pollOnce();
    await this.startRunner();
    return true;
  }

  bootoutLaunchd() {
    const r = spawnSync('/bin/launchctl',
      ['bootout', `gui/${process.getuid()}/${LAUNCHD_LABEL}`],
      { timeout: 15000 });
    this.audit('LAUNCHD_BOOTOUT', { status: r.status });
  }

  writeTakeoverRecord(trigger) {
    this.ensureDirs();
    fs.writeFileSync(path.join(this.controlDir, 'takeover.json'),
      JSON.stringify({ at_utc: nowZ(), by: 'PaperDesk.app', trigger,
                       launchd_label: LAUNCHD_LABEL,
                       note: 'RunAtLoad/KeepAlive removed from the live '
                         + 'domain; runner lifecycle now follows the app '
                         + 'per owner law' }, null, 1));
  }
}

module.exports = { RunnerController, LAUNCHD_LABEL };
