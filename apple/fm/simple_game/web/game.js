import { createState, step } from '../src/core.js';
const queued = [];
const tick = (s) => step(s, queued.length > 0 ? queued.shift() : null, Math.random);
const press = (e) => {
  const d = keyToInput(e.key);
  if (!d) { return; }
  e.preventDefault();
  if (queued.length < 3) { queued.push(d); }
};

function drawBoard(ctx, state, cell) {
    ctx.fillStyle = '#111111';
    ctx.fillRect(0, 0, state.w * cell, state.h * cell);
    ctx.fillStyle = '#ee3333';
    if (state.food !== null) {
        ctx.fillRect(state.food.x * cell, state.food.y * cell, cell, cell);
    }
    ctx.fillStyle = '#33ee66';
    state.body.forEach((c) => ctx.fillRect(c.x * cell, c.y * cell, cell, cell));
    ctx.fillStyle = '#eeeeee';
    ctx.font = '16px monospace';
    ctx.fillText('Score: ' + state.score, 8, 16);
    if (state.over) {
        ctx.fillText('GAME OVER', 8, 36);
    }
    if (state.food === null) {
        ctx.fillText('YOU WIN', 8, 56);
    }
}

function keyToInput(key) {
  const KEYS = {
    'ArrowUp': 'up',
    'ArrowDown': 'down',
    'ArrowLeft': 'left',
    'ArrowRight': 'right',
    'w': 'up',
    's': 'down',
    'a': 'left',
    'd': 'right',
    'W': 'up',
    'S': 'down',
    'A': 'left',
    'D': 'right'
  };
  return KEYS[key] || null;
}

function startLoop(state, tick, render, ms) {
  let s = state;
  render(s);
  setInterval(() => { s = tick(s); render(s); }, ms);
}

function boot(doc, cols, rows, cell) {
  const canvas = doc.getElementById('game');
  canvas.width = cols * cell;
  canvas.height = rows * cell;
  const ctx = canvas.getContext('2d');
  doc.addEventListener('keydown', (e) => press(e));
  const draw = (s) => drawBoard(ctx, s, cell);
  startLoop(createState(cols, rows), tick, draw, 120);
}

boot(document, 20, 20, 20);
