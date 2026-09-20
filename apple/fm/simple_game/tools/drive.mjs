// tools/drive.mjs - the runtime gate of the browser layer.
//
// node --check cannot prove that a renderer runs. A markdown fence opens a template
// literal, so a file of pure English passes node --check. This driver stubs the
// document, the canvas, the 2d context, the key listener and setInterval, then it
// imports web/game.js and plays a whole game.
//
// It prints ALL RUNTIME ASSERTIONS PASSED and exits 0 when every assertion holds.

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');
const CELL = 20;
const COLS = 20;
const ROWS = 20;
const PERIOD = 120;

let checks = 0;

function ok(name, cond, detail) {
  checks += 1;
  if (!cond) {
    console.error('FAIL  ' + name + (detail === undefined ? '' : '  ' + detail));
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// The probe module. It is web/game.js with the core path made absolute and with
// one export line added, so the driver can call each function on its own.
// ---------------------------------------------------------------------------

function makeProbe() {
  const src = readFileSync(resolve(ROOT, 'web/game.js'), 'utf8');
  const coreUrl = pathToFileURL(resolve(ROOT, 'src/core.js')).href;
  const patched = src.replace('../src/core.js', coreUrl);
  if (patched === src) {
    console.error('FAIL  web/game.js holds no import of ../src/core.js');
    process.exit(1);
  }
  const out = resolve(ROOT, '.build/work/game.probe.mjs');
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, patched + '\nexport { drawBoard, keyToInput, startLoop, boot };\n');
  return pathToFileURL(out).href;
}

// ---------------------------------------------------------------------------
// The fake browser
// ---------------------------------------------------------------------------

const calls = [];
const context2d = new Proxy({}, {
  get(_target, prop) {
    return (...args) => { calls.push({ fn: String(prop), args }); };
  },
  set(_target, prop, value) {
    calls.push({ fn: 'set ' + String(prop), args: [value] });
    return true;
  }
});

const canvas = {
  width: 0,
  height: 0,
  getContext(kind) { canvas.kind = kind; return context2d; }
};

const listeners = {};
const lookups = [];
const intervals = [];

globalThis.document = {
  getElementById(id) { lookups.push(id); return canvas; },
  addEventListener(type, fn) { listeners[type] = fn; }
};
globalThis.window = {
  addEventListener(type, fn) { listeners[type] = fn; }
};
globalThis.setInterval = (fn, ms) => { intervals.push({ fn, ms }); return intervals.length; };
globalThis.clearInterval = () => {};
Math.random = () => 0;

// ---------------------------------------------------------------------------
// Small readers over the recorded calls
// ---------------------------------------------------------------------------

const rects = () => calls.filter((c) => c.fn === 'fillRect').map((c) => c.args);
const texts = () => calls.filter((c) => c.fn === 'fillText').map((c) => String(c.args[0]));
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const hasRect = (want) => rects().some((r) => same(r, want));

// The page hands the whole keyboard event to the input handler, and the handler
// cancels the default action of a key that the game uses. Without that call the
// arrow keys scroll the page under the player. The stub counts every cancel.
let prevented = 0;
const ev = (key) => ({ key, preventDefault: () => { prevented += 1; } });

function frame(press) {
  if (press !== undefined) { listeners.keydown(ev(press)); }
  calls.length = 0;
  intervals[0].fn();
}

// ---------------------------------------------------------------------------
// The run
// ---------------------------------------------------------------------------

const PROBE = makeProbe();
const mod = await import(PROBE);

// 1. The boot call wired the page.
ok('the page asks for the canvas with the id game', lookups.includes('game'), lookups.join(','));
ok('the canvas width is 400', canvas.width === COLS * CELL, String(canvas.width));
ok('the canvas height is 400', canvas.height === ROWS * CELL, String(canvas.height));
ok('the canvas gives a 2d context', canvas.kind === '2d', String(canvas.kind));
ok('the page listens for keydown', typeof listeners.keydown === 'function');
ok('the game starts one interval', intervals.length === 1, String(intervals.length));
ok('the tick period is 120', intervals[0].ms === PERIOD, String(intervals[0].ms));

// 2. The first frame drew the board.
ok('the background rectangle is [0, 0, 400, 400]', hasRect([0, 0, 400, 400]), JSON.stringify(rects()[0]));
ok('the food rectangle is at the cell 5,5', hasRect([100, 100, CELL, CELL]), JSON.stringify(rects()));
ok('the head rectangle is at the cell 2,1', hasRect([40, 20, CELL, CELL]));
ok('the tail rectangle is at the cell 1,1', hasRect([20, 20, CELL, CELL]));
ok('the first frame draws one rectangle for each body cell', rects().length === 4, String(rects().length));
ok('the score text reads 0', texts().some((t) => t === 'Score: 0'), texts().join('|'));
ok('the first frame holds no game over text', !texts().some((t) => t.includes('GAME OVER')));

// 3. The key map.
const KEYMAP = [
  ['ArrowUp', 'up'], ['ArrowDown', 'down'], ['ArrowLeft', 'left'], ['ArrowRight', 'right'],
  ['w', 'up'], ['s', 'down'], ['a', 'left'], ['d', 'right'],
  ['W', 'up'], ['S', 'down'], ['A', 'left'], ['D', 'right']
];
for (const [key, want] of KEYMAP) {
  ok('the key ' + key + ' maps to ' + want, mod.keyToInput(key) === want, String(mod.keyToInput(key)));
}
ok('an unmapped key gives a false value', !mod.keyToInput('Enter'), String(mod.keyToInput('Enter')));
prevented = 0;
listeners.keydown(ev('Enter'));
ok('the page tolerates an unmapped key', true);
ok('an unmapped key keeps its default action', prevented === 0, String(prevented));

// 4. A 180 degree reversal is refused. The snake starts to the right.
frame('ArrowLeft');
ok('a key of the game loses its default action, so the page never scrolls',
  prevented === 1, String(prevented));
ok('the refused reversal keeps the snake moving right', hasRect([60, 20, CELL, CELL]), JSON.stringify(rects()));
ok('the snake left the cell 1,1', !hasRect([20, 20, CELL, CELL]), JSON.stringify(rects()));

// 5. Drive the snake onto the food at the cell 5,5 and watch the score rise.
frame();          // head 4,1
frame();          // head 5,1
frame('ArrowDown');  // head 5,2
frame();          // head 5,3
frame();          // head 5,4
frame();          // head 5,5 is the food
ok('the score rises after the snake eats', texts().some((t) => t === 'Score: 1'), texts().join('|'));
ok('the snake grew to three cells', rects().length === 5, String(rects().length));
ok('a new food cell appears at 0,0', hasRect([0, 0, CELL, CELL]), JSON.stringify(rects()));

// 6. Keep going down until the snake leaves the grid.
let over = false;
for (let i = 0; i < 40 && !over; i += 1) {
  frame();
  over = texts().some((t) => t.includes('GAME OVER'));
}
ok('the game ends when the snake leaves the grid', over, texts().join('|'));

// 7. An ended game stays ended and keeps its score.
frame();
ok('the ended game keeps the game over text', texts().some((t) => t.includes('GAME OVER')));
ok('the ended game keeps a score of 1 or more',
  texts().some((t) => t.startsWith('Score: ') && Number(t.slice(7)) >= 1), texts().join('|'));

// 8. The input queue holds both keys of a fast corner turn.
// A single slot would keep the last key only, and turn() then refuses it as a
// 180 degree reversal, so both taps would be lost. A fresh instance of the module
// gives a new game, because the game above already ended.
await import(PROBE + '?fresh=1');
const qi = intervals.length - 1;
ok('the fresh game started its own interval', qi === 1, String(intervals.length));
const qframe = (keys) => {
  for (const k of keys) { listeners.keydown(ev(k)); }
  calls.length = 0;
  intervals[qi].fn();
};
qframe(['ArrowUp', 'ArrowLeft']);
ok('the first key of a fast pair turns the snake up on this tick',
  hasRect([40, 0, CELL, CELL]), JSON.stringify(rects()));
qframe([]);
ok('the second key of the pair turns the snake left on the next tick',
  hasRect([20, 0, CELL, CELL]), JSON.stringify(rects()));

console.log(checks + ' runtime assertions ran.');
console.log('ALL RUNTIME ASSERTIONS PASSED');
