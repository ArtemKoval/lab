import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createState } from '../src/createState.js';

test('start body', () => {
  assert.deepEqual(createState(20, 20).body, [{ x: 2, y: 1 }, { x: 1, y: 1 }]);
});

test('start direction', () => {
  assert.equal(createState(20, 20).dir, 'right');
});

test('start food', () => {
  assert.deepEqual(createState(20, 20).food, { x: 5, y: 5 });
});

test('start score', () => {
  assert.equal(createState(20, 20).score, 0);
});

test('not over', () => {
  assert.equal(createState(20, 20).over, false);
});

test('grid width', () => {
  assert.equal(createState(12, 9).w, 12);
});

test('grid height', () => {
  assert.equal(createState(12, 9).h, 9);
});
