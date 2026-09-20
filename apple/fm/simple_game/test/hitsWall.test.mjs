import { test } from 'node:test';
import assert from 'node:assert/strict';
import { hitsWall } from '../src/hitsWall.js';

test('inside', () => {
  assert.equal(hitsWall({ x: 0, y: 0 }, 4, 4), false);
});

test('far corner', () => {
  assert.equal(hitsWall({ x: 3, y: 3 }, 4, 4), false);
});

test('x past edge', () => {
  assert.equal(hitsWall({ x: 4, y: 1 }, 4, 4), true);
});

test('y past edge', () => {
  assert.equal(hitsWall({ x: 1, y: 4 }, 4, 4), true);
});

test('negative x', () => {
  assert.equal(hitsWall({ x: -1, y: 1 }, 4, 4), true);
});

test('negative y', () => {
  assert.equal(hitsWall({ x: 1, y: -1 }, 4, 4), true);
});
