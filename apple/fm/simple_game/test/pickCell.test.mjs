import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pickCell } from '../src/pickCell.js';

test('empty list', () => {
  assert.equal(pickCell([], () => 0), null);
});

test('rng zero', () => {
  assert.deepEqual(pickCell([{ x: 0, y: 0 }, { x: 1, y: 0 }], () => 0), { x: 0, y: 0 });
});

test('rng near one', () => {
  assert.deepEqual(pickCell([{ x: 0, y: 0 }, { x: 1, y: 0 }], () => 0.99), { x: 1, y: 0 });
});

test('middle of three', () => {
  assert.deepEqual(pickCell([{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 2, y: 0 }], () => 0.5), { x: 1, y: 0 });
});

test('last of three', () => {
  assert.deepEqual(pickCell([{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 2, y: 0 }], () => 0.99), { x: 2, y: 0 });
});
