'use strict';
// Lifecycle safety battery (owner audit P0-4 regression):
//   * identity binding: pid + process-start token (lstart) + command must
//     match OUR ops_service on OUR data root before any signal;
//   * foreign command / wrong data root / sandbox mismatch -> refuse;
//   * PID reuse (bound lstart != current lstart) -> refuse + audit;
//   * unexplained held service.lock -> stop refused (fail-closed);
//   * positive control: a process carrying our command signature is
//     gracefully SIGTERMed and the stop verifies clean.
// Node-level, no launchd touched. Exits 0 iff all checks pass.
const { spawn, spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { RunnerController } = require('./main/runner');

const PYTHON = '/Users/hoangminhlong/my-quantitative/.venv/bin/python';
const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'pd-lifecycle-'));
const results = [];
const check = (cond, name) => {
  results.push({ name, pass: !!cond });
  console.log(`[${cond ? 'PASS' : 'FAIL'}] ${name}`);
};
const sleep = ms => new Promise(r => setTimeout(r, ms));

// A REAL live process whose command line carries our marker signature
// (ops_service + --data-root <root> + --sandbox) without being a runner.
function spawnMarkerProcess() {
  const p = spawn(PYTHON, ['-c', 'import time; time.sleep(120)',
                           'ops_service',
                           '--data-root', tmpRoot, '--sandbox'],
                  { stdio: 'ignore' });
  return p;
}

(async () => {
  const ctl = new RunnerController({ dataRoot: tmpRoot, sandbox: true,
    worktreeDir: tmpRoot });

  // 1. identity rejection: a process without ops_service marker
  const foreign = spawn('/bin/sleep', ['120'], { stdio: 'ignore' });
  await sleep(400);
  const fid = ctl.processIdentity(foreign.pid);
  check(!!fid && fid.lstart.length > 0, 'processIdentity reads lstart token');
  check(!ctl.identityIsOurs(foreign.pid, fid),
    'identity: foreign command (sleep) rejected');
  // wrong data root
  const wrongRoot = spawn(PYTHON, ['-c', 'import time; time.sleep(120)',
    'ops_service', '--data-root', '/somewhere/else', '--sandbox'],
    { stdio: 'ignore' });
  await sleep(400);
  check(!ctl.identityIsOurs(wrongRoot.pid,
    ctl.processIdentity(wrongRoot.pid)),
    'identity: different --data-root rejected');

  // 2. positive: marker process passes identity gates
  const marker = spawnMarkerProcess();
  await sleep(600);
  const mid = ctl.processIdentity(marker.pid);
  check(ctl.identityIsOurs(marker.pid, mid),
    'identity: our signature (ops_service + data-root + --sandbox) accepted');

  // 3. PID reuse guard: bind a STALE lstart, keep the live pid
  ctl.state = { s: 'attached', pid: marker.pid, source: 'external' };
  ctl.attachedIdentity = { pid: marker.pid, lstart: 'STALE TOKEN 1970',
    command: mid.command };
  check(ctl.ownedRunnerAlive() === false,
    'pid-reuse: bound lstart != live lstart -> ownedRunnerAlive false');
  check(ctl.state.s === 'detached',
    'pid-reuse: state dropped to detached');
  const reuseAudits = (() => {
    try {
      return fs.readFileSync(ctl.controllerLogPath, 'utf8')
        .split('\\n').filter(l => l.includes('PID_REUSE_REFUSED')).length;
    } catch (e) { return 0; }
  })();
  check(reuseAudits >= 1, 'pid-reuse: PID_REUSE_REFUSED journaled');

  // 4. graceful stop positive control: correct identity -> clean stop
  const marker2 = spawnMarkerProcess();
  await sleep(600);
  const mid2 = ctl.processIdentity(marker2.pid);
  ctl.state = { s: 'attached', pid: marker2.pid, source: 'external' };
  ctl.attachedIdentity = { pid: marker2.pid, lstart: mid2.lstart,
                           command: mid2.command };
  const ok = await ctl.gracefulStopRunner('unit-test');
  check(ok === true && !ctl.pidAlive(marker2.pid),
    'stop: verified-identity external runner SIGTERMed cleanly');
  check(ctl.state.s === 'stopped', 'stop: state = stopped');

  // 5. unexplained held lock -> refuse to stop/quit
  const lockDir = path.join(tmpRoot, 'lockprobe');
  fs.mkdirSync(lockDir, { recursive: true });
  const lockPath = path.join(lockDir, 'service.lock');
  const holder = spawn(PYTHON,
    [path.join(__dirname, 'helpers', 'opslock.py'), 'hold', lockPath,
     '/bin/sleep', '30'], { stdio: 'ignore' });
  await sleep(800);
  const ctl2 = new RunnerController({ dataRoot: tmpRoot, sandbox: true,
    worktreeDir: tmpRoot });
  ctl2.serviceLockPath = lockPath;
  const refused = await ctl2.gracefulStopRunner('unit-test');
  check(refused === false,
    'fail-closed: unexplained held service.lock -> stop refused');
  check(ctl2.state.s !== 'stopping', 'fail-closed: no stopping state leak');

  // 6. bootout-failure path (simulated): launchd still loaded after bootout
  const marker3 = spawnMarkerProcess();
  await sleep(600);
  const mid3 = ctl.processIdentity(marker3.pid);
  ctl.state = { s: 'attached', pid: marker3.pid, source: 'launchd' };
  ctl.attachedIdentity = { pid: marker3.pid, lstart: mid3.lstart,
                           command: mid3.command };
  ctl.launchdState = () => ({ loaded: true, pid: marker3.pid }); // stub
  const bootoutBlocked = await ctl.gracefulStopRunner('unit-test');
  check(bootoutBlocked === false && ctl.pidAlive(marker3.pid),
    'fail-closed: bootout failure aborts stop, runner left RUNNING');
  check(ctl.state.s === 'attached',
    'fail-closed: state restored to attached (app must stay open)');
  process.kill(marker3.pid, 'SIGTERM');   // cleanup the stub fixture

  [foreign, wrongRoot, marker, marker2, marker3, holder].forEach(p => {
    try { if (p && p.exitCode === null && p.pid) process.kill(p.pid,
      'SIGKILL'); } catch (e) {}
  });

  fs.writeFileSync(path.join(tmpRoot, 'results.json'),
    JSON.stringify(results, null, 1));
  const fails = results.filter(r => !r.pass).length;
  console.log(`lifecycle safety: ${results.length - fails}/`
    + `${results.length} pass`);
  process.exit(fails ? 1 : 0);
})();
