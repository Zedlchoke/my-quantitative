'use strict';
// Regression for the renderer leak: each redraw used to keep its canvas alive
// through a new global resize listener. No Electron or live runner is needed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const resizeListeners = new Set();
const context2d = {
  scale() {}, clearRect() {}, beginPath() {}, moveTo() {}, lineTo() {},
  stroke() {},
};
function element(tag) {
  return {
    tag, style: {}, clientWidth: 800, className: '',
    children: [],
    set innerHTML(value) { this.children = []; this.html = value; },
    get innerHTML() { return this.html || ''; },
    appendChild(child) { this.children.push(child); return child; },
    querySelectorAll() { return []; },
    addEventListener() {},
    getContext() { return context2d; },
  };
}
const browser = {
  devicePixelRatio: 2,
  addEventListener(name, fn) {
    if (name === 'resize') resizeListeners.add(fn);
  },
  removeEventListener(name, fn) {
    if (name === 'resize') resizeListeners.delete(fn);
  },
};
vm.runInNewContext(
  fs.readFileSync(path.join(__dirname, 'renderer/chart.js'), 'utf8'),
  { window: browser,
    document: { createElement: element, documentElement: {} },
    getComputedStyle: () => ({ getPropertyValue: () => '#aaaaaa' }),
  },
);
const container = element('div');
for (let i = 0; i < 1000; i++) {
  browser.EquityChart.render(container, [], { height: 230 });
  assert.equal(resizeListeners.size, 1, `resize listener leak at redraw ${i}`);
}
for (const listener of resizeListeners) listener();
assert.equal(resizeListeners.size, 1);
process.stdout.write('chart lifecycle: 1000 redraws, one resize listener\n');
