// tools/derive.mjs - the killing input finder of the mutation gate.
//
// The model cannot find an input that separates a mutant from the original, and it
// cannot compute an expected value. This tool does both. It reads the SURVIVOR lines
// of .build/feedback/mutation.txt on the standard input. For each survivor it writes
// the mutant to a copy of src/, imports the original and the mutant, and walks a fixed
// domain until the two results differ. The expected value always comes from the ORIGINAL.
//
// Output for one survivor is one of
//   EQUIVALENT <location> <reason>      the whole domain gives the same result
//   UNPROVEN <location> <reason>        the build could not judge the mutant
//   FILL <location>
//   NAME = <the test name>
//   BODY = <one assert call>
//   ENDFILL
//
// EQUIVALENT is a claim that no test can kill the mutant, and the mutation gate can
// accept a red run on that claim. A mutant that does not load is therefore never
// EQUIVALENT. It is UNPROVEN, and the gate reads UNPROVEN as red.
//
// A stryker diff can hold more than one minus line. gate_mutation writes the whole
// block to .build/feedback/mutants/<n>.diff, and this tool replaces the whole span.
// A mutant that is rebuilt from the first minus line alone does not parse.

import { readFileSync, writeFileSync, mkdirSync, rmSync, readdirSync, copyFileSync } from 'node:fs';
import { dirname, resolve, basename } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');
const WORK = resolve(ROOT, '.build/work/derive');

// ---------------------------------------------------------------------------
// The domain of each unit. Every entry gives one fresh argument tuple.
// A fresh tuple matters, because a tuple can hold a counter function.
// ---------------------------------------------------------------------------

const CELLS = [];
for (let y = -1; y <= 3; y += 1) { for (let x = -1; x <= 3; x += 1) { CELLS.push({ x, y }); } }
const CELLS5 = [];
for (let y = -1; y <= 5; y += 1) { for (let x = -1; x <= 5; x += 1) { CELLS5.push({ x, y }); } }
const DIRS = ['up', 'down', 'left', 'right'];
const BODIES = [[], [{ x: 1, y: 1 }], [{ x: 0, y: 1 }, { x: 2, y: 1 }]];
const GRIDS = [[2, 1], [3, 1], [1, 2], [2, 2], [4, 4]];
const RNGS = [0, 0.34, 0.5, 0.99];
const S = () => ({ w: 3, h: 3, body: [{ x: 2, y: 1 }], dir: 'right', food: { x: 2, y: 2 }, score: 0 });
// D is a three cell snake. Its tail at {x:2,y:2} leaves that cell on the same tick,
// so a head that enters it lives. DEAT puts the food on the tail, so the tail stays.
const D = () => ({ w: 5, h: 5, body: [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }], food: { x: 4, y: 4 } });
const DEAT = () => ({ w: 5, h: 5, body: [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }], food: { x: 2, y: 2 } });
// FULL has two cells and one of them holds the snake, so one meal fills the board.
const FULL = () => ({ w: 1, h: 2, body: [{ x: 0, y: 1 }], dir: 'up', food: { x: 0, y: 0 }, score: 0 });

function cross(...lists) {
  return lists.reduce((acc, list) => acc.flatMap((a) => list.map((b) => [...a, b])), [[]]);
}

const DOMAIN = {
  samePos: () => cross(CELLS, CELLS),
  nextHead: () => cross(CELLS, DIRS),
  turn: () => cross(DIRS, [...DIRS, null, 'x']),
  hitsWall: () => cross(CELLS, [1, 4, 10], [1, 4, 10]),
  hitsSelf: () => cross(CELLS, BODIES),
  growOrMove: () => cross(BODIES, [{ x: 2, y: 1 }, { x: 0, y: 0 }], [true, false]),
  freeCells: () => cross([[], [{ x: 0, y: 0 }], [{ x: 1, y: 0 }]], GRIDS).map(([o, g]) => [o, g[0], g[1]]),
  pickCell: () => cross([[], [{ x: 0, y: 0 }], [{ x: 0, y: 0 }, { x: 1, y: 0 }]], RNGS)
    .map(([free, r]) => [free, () => r]),
  placeFood: () => cross([[], [{ x: 0, y: 0 }]], GRIDS, RNGS).map(([o, g, r]) => [o, g[0], g[1], () => r]),
  createState: () => [[8, 8], [12, 9], [20, 20]],
  isDead: () => CELLS5.map((c) => [c, D()]).concat(CELLS5.map((c) => [c, DEAT()])),
  advance: () => cross(DIRS, [{ x: 2, y: 0 }, { x: 2, y: 2 }, { x: 1, y: 1 }], RNGS)
    .map(([d, head, r]) => [S(), d, head, () => r])
    .concat(DIRS.map((d) => [FULL(), d, { x: 0, y: 0 }, () => 0])),
  step: () => cross([...DIRS, null, 'x'], RNGS).map(([i, r]) => [S(), i, () => r])
};

// ---------------------------------------------------------------------------
// Printing an argument tuple back as JavaScript source
// ---------------------------------------------------------------------------

function show(value) {
  if (typeof value === 'function') { return '() => ' + show(value()); }
  if (value === null) { return 'null'; }
  if (value === undefined) { return 'undefined'; }
  if (Array.isArray(value)) { return '[' + value.map(show).join(',') + ']'; }
  if (typeof value === 'object') {
    return '{' + Object.keys(value).map((k) => k + ':' + show(value[k])).join(',') + '}';
  }
  return JSON.stringify(value);
}

const deep = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// ---------------------------------------------------------------------------
// The mutant copy
// ---------------------------------------------------------------------------

let round = 0;

// readDiff gives the whole minus block and the whole plus block of one survivor.
function readDiff(n) {
  try {
    const rows = readFileSync(resolve(ROOT, '.build/feedback/mutants', n + '.diff'), 'utf8')
      .split('\n').filter((r) => r.length > 0);
    const minus = rows.filter((r) => r[0] === '-').map((r) => r.slice(1));
    const plus = rows.filter((r) => r[0] === '+').map((r) => r.slice(1));
    if (minus.length > 0) { return { minus, plus }; }
  } catch {
    return null;
  }
  return null;
}

function makeMutant(file, line, minus, plus) {
  round += 1;
  const dir = resolve(WORK, 'm' + round);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  for (const name of readdirSync(resolve(ROOT, 'src'))) {
    copyFileSync(resolve(ROOT, 'src', name), resolve(dir, name));
  }
  const target = resolve(dir, basename(file));
  const lines = readFileSync(target, 'utf8').split('\n');
  const i = line - 1;
  if (i < 0 || i >= lines.length) { return null; }
  if (minus.length === 0 || minus[0].trim() === '') { return null; }
  if (minus.length === 1) {
    const a = minus[0].trim();
    const b = plus.length > 0 ? plus[0].trim() : '';
    if (!lines[i].includes(a)) { return null; }
    lines[i] = lines[i].replace(a, b);
  } else {
    for (let k = 0; k < minus.length; k += 1) {
      if (i + k >= lines.length) { return null; }
      if (lines[i + k].trim() !== minus[k].trim()) { return null; }
    }
    const indent = (lines[i].match(/^\s*/) || [''])[0];
    lines.splice(i, minus.length, ...plus.map((t) => indent + t.trim()));
  }
  writeFileSync(target, lines.join('\n'));
  return pathToFileURL(target).href;
}

// ---------------------------------------------------------------------------
// The search
// ---------------------------------------------------------------------------

function call(fn, args) {
  try { return { value: fn(...args) }; } catch (e) { return { error: String(e && e.message) }; }
}

async function findKiller(unit, mutantUrl) {
  // NOTE: the oracle here is the implementation, not the contract. A mutant gives
  // no expected value, so the live unit supplies it. The unit gate runs first, so the
  // unit already satisfies every CASES row of its contract. A wrong but
  // contract-conformant unit still yields a test that locks in the wrong behaviour.
  // See PLAN.md 2.4. This is the one place the build is not blind.
  const goodUrl = pathToFileURL(resolve(ROOT, 'src', unit + '.js')).href;
  const good = (await import(goodUrl))[unit];
  const badModule = await import(mutantUrl + '?v=' + round);
  const bad = badModule[unit];
  if (typeof good !== 'function') { throw new Error('src/' + unit + '.js exports no function'); }
  if (typeof bad !== 'function') { throw new Error('the mutant of ' + unit + ' exports no function'); }
  const make = DOMAIN[unit];
  if (!make) { throw new Error('the unit ' + unit + ' has no domain'); }
  for (const args of make()) {
    const g = call(good, args);
    const b = call(bad, args);
    if (!deep(g, b)) {
      if (g.error !== undefined) { continue; }
      return { args, expected: g.value };
    }
  }
  return null;
}

function assertLine(unit, args, expected) {
  const call2 = unit + '(' + args.map(show).join(', ') + ')';
  const kind = (expected !== null && typeof expected === 'object') ? 'deepEqual' : 'equal';
  return 'assert.' + kind + '(' + call2 + ', ' + show(expected) + ');';
}

// ---------------------------------------------------------------------------
// The main pass
// ---------------------------------------------------------------------------

const text = readFileSync(0, 'utf8');
const out = [];
let n = 0;

const clip = (t) => String(t).replace(/\s+/g, ' ').slice(0, 140);

for (const row of text.split('\n')) {
  const m = row.match(
    /^SURVIVOR (\d+) \| MUTATOR (\S+) \| LOC (\S+)(?: \| SPAN \d+)? \| MINUS (.*) \| PLUS (.*)$/);
  if (!m) { continue; }
  const [, index, mutator, loc, minus1, plus1] = m;
  const parts = loc.split(':');
  const file = parts[0];
  const line = Number(parts[1]);
  const unit = basename(file, '.js');
  if (!DOMAIN[unit]) { out.push('UNPROVEN ' + loc + ' the unit ' + unit + ' has no domain'); continue; }
  const block = readDiff(index) || { minus: [minus1], plus: [plus1] };
  const url = makeMutant(file, line, block.minus, block.plus);
  if (!url) { out.push('UNPROVEN ' + loc + ' the build cannot apply the mutant text'); continue; }
  let hit = null;
  let failure = null;
  try { hit = await findKiller(unit, url); } catch (e) { failure = clip(e && e.message ? e.message : e); }
  if (failure !== null) { out.push('UNPROVEN ' + loc + ' the mutant does not load: ' + failure); continue; }
  if (!hit) { out.push('EQUIVALENT ' + loc + ' no input of the domain separates the mutant'); continue; }
  n += 1;
  out.push('FILL ' + loc);
  out.push('NAME = kill ' + n + ' ' + mutator + ' in ' + unit);
  out.push('BODY = ' + assertLine(unit, hit.args, hit.expected));
  out.push('ENDFILL');
}

process.stdout.write(out.join('\n') + (out.length ? '\n' : ''));
