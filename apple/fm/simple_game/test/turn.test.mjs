import { test } from 'node:test';
import assert from 'node:assert/strict';
import { turn } from '../src/turn.js';

test('turn left', () => {
  assert.equal(turn('up', 'left'), 'left');
});

test('turn right', () => {
  assert.equal(turn('up', 'right'), 'right');
});

test('turn up', () => {
  assert.equal(turn('left', 'up'), 'up');
});

test('reversal from right', () => {
  assert.equal(turn('right', 'left'), 'right');
});

test('reversal from up', () => {
  assert.equal(turn('up', 'down'), 'up');
});

test('reversal from down', () => {
  assert.equal(turn('down', 'up'), 'down');
});

test('no key press', () => {
  assert.equal(turn('up', null), 'up');
});

test('unknown key', () => {
  assert.equal(turn('up', 'x'), 'up');
});
