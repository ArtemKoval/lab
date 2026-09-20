import { test } from 'node:test';
import assert from 'node:assert/strict';
import { freeCells } from '../src/freeCells.js';

test('none taken', () => {
  assert.deepEqual(freeCells([], 2, 1), [{ x: 0, y: 0 }, { x: 1, y: 0 }]);
});

test('one taken', () => {
  assert.deepEqual(freeCells([{ x: 0, y: 0 }], 2, 1), [{ x: 1, y: 0 }]);
});

test('full grid', () => {
  assert.deepEqual(freeCells([{ x: 0, y: 0 }, { x: 1, y: 0 }], 2, 1), []);
});

test('tall grid', () => {
  assert.deepEqual(freeCells([], 1, 2), [{ x: 0, y: 0 }, { x: 0, y: 1 }]);
});

test('gap in a row', () => {
  assert.deepEqual(freeCells([{ x: 1, y: 0 }], 3, 1), [{ x: 0, y: 0 }, { x: 2, y: 0 }]);
});
