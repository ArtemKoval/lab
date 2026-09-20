import { test } from 'node:test';
import assert from 'node:assert/strict';
import { samePos } from '../src/samePos.js';

test('equal cells', () => {
  assert.equal(samePos({ x: 1, y: 2 }, { x: 1, y: 2 }), true);
});

test('x differs', () => {
  assert.equal(samePos({ x: 1, y: 2 }, { x: 2, y: 2 }), false);
});

test('y differs', () => {
  assert.equal(samePos({ x: 1, y: 2 }, { x: 1, y: 3 }), false);
});

test('both differ', () => {
  assert.equal(samePos({ x: 0, y: 0 }, { x: 3, y: 3 }), false);
});
