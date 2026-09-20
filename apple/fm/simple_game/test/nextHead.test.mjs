import { test } from 'node:test';
import assert from 'node:assert/strict';
import { nextHead } from '../src/nextHead.js';

test('right', () => {
  assert.deepEqual(nextHead({ x: 2, y: 2 }, 'right'), { x: 3, y: 2 });
});

test('left', () => {
  assert.deepEqual(nextHead({ x: 2, y: 2 }, 'left'), { x: 1, y: 2 });
});

test('up', () => {
  assert.deepEqual(nextHead({ x: 2, y: 2 }, 'up'), { x: 2, y: 1 });
});

test('down', () => {
  assert.deepEqual(nextHead({ x: 2, y: 2 }, 'down'), { x: 2, y: 3 });
});

test('negative x', () => {
  assert.deepEqual(nextHead({ x: 0, y: 0 }, 'left'), { x: -1, y: 0 });
});

test('offset cell', () => {
  assert.deepEqual(nextHead({ x: 3, y: 1 }, 'down'), { x: 3, y: 2 });
});
