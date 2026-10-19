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
  // Process identity = (pid, lstart token, command). Recorded at ATTACH and
  // re-verified before ANY signal: a recycled PID with a different lstart or
  // a command that is not OUR ops_service on OUR data root is never signaled
  // (foreign-worker / PID-reuse guard, mirrors the heavy-lock registry).
  processIdentity(pid) {
    // two separate ps calls: combined output pads lstart and command with
    // spaces on ONE line, which is ambiguous to split
    const l = spawnSync('/bin/ps', ['-p', String(pid), '-o', 'lstart='],
                        { encoding: 'utf8', timeout: 10000 });
    const c = spawnSync('/bin/ps', ['-p', String(pid), '-o', 'command='],
                        { encoding: 'utf8', timeout: 10000 });
    if (l.status !== 0 || c.status !== 0) return null;
    const lstart = String(l.stdout).trim();
    const command = String(c.stdout).trim();
    if (!lstart || !command) return null;
    return { lstart, command };
  }

  identityIsOurs(pid, ident) {
    if (!ident) return false;
    if (!ident.command.includes('ops_service')) return false;
    if (ident.command.includes(this.dataRoot)) {
      // explicit data-root form (app-spawned child / manual runner)
      if (this.sandbox && !ident.command.includes('--sandbox')) return false;
      if (!this.sandbox && ident.command.includes('--sandbox')) return false;
      return true;
    }
    // launchd plist form: bare `python -m research.papertrade_exec.ops_service`
    // (module default data root, plist WorkingDirectory binds the worktree).
    // Authoritative ONLY when OUR launchd label currently reports exactly
    // this pid (launchd's live mapping — inherently PID-reuse-safe) AND the
    // plist binds our worktree to our runner module.
    if (!ident.command.includes('--data-root') && this.launchdOwned) {
      const ld = this.launchdState();
      if (ld.loaded && ld.pid === pid && this.launchdPlistBindsUs()) {
        this.audit('IDENTITY_VIA_LAUNCHD_PLIST', { pid });
        return true;
      }
    }
    return false;
  }

  /// Cached check: ~/Library/LaunchAgents/<label>.plist ProgramArguments end
  /// with `-m research.papertrade_exec.ops_service` and its WorkingDirectory
  /// equals this app's runner worktree.
  launchdPlistBindsUs() {
    if (this._plistBindsUs !== undefined) return this._plistBindsUs;
    try {
      const r = spawnSync('/usr/bin/plutil', ['-convert', 'json', '-o', '-',
        `${process.env.HOME}/Library/LaunchAgents/${LAUNCHD_LABEL}.plist`],
        { encoding: 'utf8', timeout: 10000 });
      const d = JSON.parse(String(r.stdout));
      const argv = d.ProgramArguments || [];
      const okArgs = argv.length >= 3
        && argv[argv.length - 2] === '-m'
        && argv[argv.length - 1] === 'research.papertrade_exec.ops_service';
      const cwd = decodeURIComponent(
        (this.worktreeDir && this.worktreeDir.pathname)
          || String(this.worktreeDir || ''));
      this._plistBindsUs = !!(okArgs && d.WorkingDirectory
                               && (d.WorkingDirectory === cwd
                                   || cwd.endsWith(d.WorkingDirectory)
                                   || d.WorkingDirectory.endsWith(cwd)));
    } catch (e) {
      this._plistBindsUs = false;
    }
    return this._plistBindsUs;
  }

  pollOnce() {
    this.heartbeat = this.readHeartbeat();
    const ld = this.launchdState();
    this.launchdOwned = ld.loaded;
    if (this.state.s === 'stopping' || this.state.s === 'starting') return;
    const hb = this.heartbeat;
    if (hb && hb.pid && hb.isFresh && this.pidAlive(hb.pid)
        && this.pidIsOpsService(hb.pid)) {
      // NOTE: the venv python shim re-execs the interpreter with a NEW
      // pid, so heartbeat.pid may differ from child.pid — ownership is
      // decided by identity (command + data-root + sandbox mode); a live
      // child launcher makes it 'child' rather than 'external'.
      const oursChild = this.child && this.child.exitCode === null
        && this.identityIsOurs(hb.pid,
            this.processIdentity(hb.pid) || {});
      const source = oursChild ? 'child'
        : (ld.loaded ? 'launchd' : 'external');
      // (re)bind the identity token whenever the attached pid changes
      if (this.state.s !== 'attached' || this.state.pid !== hb.pid
          || this.state.source !== source) {
        this.attachedIdentity = { pid: hb.pid,
                                  ...(this.processIdentity(hb.pid) || {}) };
        this.state = { s: 'attached', pid: hb.pid, source };
        this.audit('ATTACH', { pid: hb.pid, source,
                               lstart: this.attachedIdentity.lstart });
      }
    } else if (this.child && this.child.exitCode === null) {
      // child up, heartbeat not ready yet
    } else if (this.state.s === 'attached' && hb && hb.pid
               && !this.pidAlive(hb.pid)) {
      this.state = { s: 'detached', pid: null, source: null };
      this.attachedIdentity = null;
      this.audit('RUNNER_GONE', { pid: hb.pid });
    } else if (this.state.s === 'probing') {
      this.state = { s: 'detached', pid: null, source: null };
    }
  }

  /// True only when the attached runner is STILL the exact process we bound
  /// at ATTACH (alive, same lstart token, our command, our data root).
  ownedRunnerAlive() {
    if (this.state.s !== 'attached' || !this.state.pid) return false;
    const pid = this.state.pid;
    if (!this.pidAlive(pid)) return false;
    const ident = this.processIdentity(pid);
    if (!this.identityIsOurs(pid, ident)) {
      this.audit('IDENTITY_LOST', { pid, ident: ident || null });
      return false;
    }
    if (this.attachedIdentity && this.attachedIdentity.lstart
        && ident.lstart !== this.attachedIdentity.lstart) {
      // PID was recycled between ATTACH and now — never signal it
      this.audit('PID_REUSE_REFUSED', { pid,
        bound_lstart: this.attachedIdentity.lstart,
        now_lstart: ident.lstart });
      this.state = { s: 'detached', pid: null, source: null };
      this.attachedIdentity = null;
      return false;
    }
    return true;
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
        // readiness is IDENTITY-based: the venv shim re-execs, so
        // heartbeat.pid may differ from the launcher pid
        const hb = this.readHeartbeat();
        if (hb && hb.pid && hb.isFresh && this.pidAlive(hb.pid)
            && this.identityIsOurs(hb.pid,
                this.processIdentity(hb.pid) || {})) {
          this.state = { s: 'attached', pid: hb.pid, source: 'child' };
          this.attachedIdentity = { pid: hb.pid,
            ...(this.processIdentity(hb.pid) || {}) };
          this.lastAction = `Paper runner started (pid ${hb.pid})`;
          this.audit('CHILD_READY', { launcher_pid: child.pid,
                                      runner_pid: hb.pid });
          return resolve(true);
        }
        if (child.exitCode !== null) {
          // launcher exited but a verified runner holds the lock: adopt it
          const hb2 = this.readHeartbeat();
          if (hb2 && hb2.pid && hb2.isFresh && this.pidAlive(hb2.pid)
              && this.identityIsOurs(hb2.pid,
                  this.processIdentity(hb2.pid) || {})) {
            this.state = { s: 'attached', pid: hb2.pid, source: 'child' };
            this.attachedIdentity = { pid: hb2.pid,
              ...(this.processIdentity(hb2.pid) || {}) };
            this.audit('CHILD_READY', { launcher_pid: child.pid,
                                        runner_pid: hb2.pid,
                                        note: 'launcher re-exec adopt' });
            return resolve(true);
          }
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

  /// Quit law with fail-closed safety: returns true ONLY when the runner is
  /// verifiably stopped AND the flock is released. Any verification failure
  /// (identity lost, PID reuse, bootout failure, lock still held) returns
  /// false and the caller MUST keep the app open and surface the error —
  /// a half-stopped lifecycle is worse than a running runner.
  async gracefulStopRunner(reason) {
    this.pollOnce();
    if (this.state.s !== 'attached') {
      this.lastAction = 'No runner to stop';
      // even with nothing attached, refuse on a held lock we cannot explain
      if (this.flockHeld(this.serviceLockPath)) {
        this.audit('STOP_REFUSED_LOCK_HELD_UNEXPLAINED', {});
        this.lastAction = 'service.lock held by an unverified process — '
          + 'not stopping, investigate manually';
        return false;
      }
      return true;
    }
    if (!this.ownedRunnerAlive()) {
      this.audit('STOP_REFUSED_IDENTITY', { pid: this.state.pid });
      this.lastAction = 'Runner identity unverified — refusing to signal';
      this.state = { s: 'detached', pid: null, source: null };
      return false;
    }
    const { pid, source } = this.state;
    this.state = { s: 'stopping', pid, source };
    this.lastAction = 'Stopping paper runner gracefully…';
    this.audit('GRACEFUL_STOP_BEGIN', { pid, source, reason,
      lstart: this.attachedIdentity ? this.attachedIdentity.lstart : null });
    if (source === 'launchd') {
      // launchd KeepAlive would resurrect the runner — the agent MUST leave
      // the domain first; a failed bootout aborts the stop (fail-closed).
      // bootout acceptance is async: poll the domain for up to 5 s before
      // declaring failure (a too-early print can still see the label).
      this.bootoutLaunchd();
      let ld = this.launchdState();
      for (let i = 0; i < 10 && ld.loaded; i++) {
        await this.sleep(500);
        ld = this.launchdState();
      }
      if (ld.loaded) {
        this.audit('LAUNCHD_BOOTOUT_FAILED', { pid });
        this.lastAction = 'launchctl bootout failed — runner left RUNNING '
          + '(KeepAlive would resurrect it). App stays open.';
        this.state = { s: 'attached', pid, source };
        return false;
      }
      this.writeTakeoverRecord('quit');
    }
    const wasChild = this.child && this.child.pid === pid;
    this.child = null;
    try { process.kill(pid, 'SIGTERM'); } catch (e) {
      // ESRCH: already gone (e.g. bootout terminated it first) — fine
    }
    const deadline = Date.now() + 8000;
    while (Date.now() < deadline && this.pidAlive(pid)) await this.sleep(250);
    let clean = !this.pidAlive(pid);
    if (!clean) {
      // last resort: SIGKILL only if the process is STILL verifiably ours
      if (this.ownedRunnerAlive() || this.identityIsOurs(pid,
        this.processIdentity(pid))) {
        try { process.kill(pid, 'SIGKILL'); } catch (e) {}
        this.audit('GRACEFUL_STOP_FORCED_KILL', { pid });
        const kdeadline = Date.now() + 3000;
        while (Date.now() < kdeadline && this.pidAlive(pid)) {
          await this.sleep(200);
        }
        clean = !this.pidAlive(pid);
      } else {
        this.audit('FORCE_KILL_REFUSED_IDENTITY', { pid });
        this.lastAction = 'Process identity changed during stop — '
          + 'refused to force-kill';
        this.state = { s: 'failed', pid: null, source: null,
                       error: 'identity lost during stop' };
        return false;
      }
    }
    const flDeadline = Date.now() + 3000;
    while (Date.now() < flDeadline && this.flockHeld(this.serviceLockPath)) {
      await this.sleep(200);
    }
    const lockFree = !this.flockHeld(this.serviceLockPath);
    if (wasChild && this.child && this.child.pid === pid) this.child = null;
    this.state = lockFree && clean
      ? { s: 'stopped', pid: null, source: null }
      : { s: 'failed', pid: null, source: null,
          error: clean ? 'service.lock still held after stop'
                       : 'runner did not exit' };
    this.lastAction = clean && lockFree
      ? 'Paper runner stopped gracefully (SERVICE_STOP journaled)'
      : clean ? 'Runner exited but service.lock is STILL HELD — not safe'
              : 'Runner did not exit in time';
    this.audit('GRACEFUL_STOP_END', { pid, clean, lock_free: lockFree });
    this.heartbeat = this.readHeartbeat();
    return clean && lockFree;
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
