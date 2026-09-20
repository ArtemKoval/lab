import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isDead } from '../src/isDead.js';

const D = {w:5,h:5,body:[{x:1,y:1},{x:2,y:1},{x:2,y:2}],food:{x:4,y:4}};

test('wall on x', () => {
  assert.equal(isDead({x:-1,y:0},D), true);
});

test('wall on y', () => {
  assert.equal(isDead({x:0,y:5},D), true);
});

test('body cell', () => {
  assert.equal(isDead({x:2,y:1},D), true);
});

test('free cell', () => {
  assert.equal(isDead({x:3,y:3},D), false);
});

test('tail cell is free', () => {
  assert.equal(isDead({x:2,y:2},D), false);
});

test('tail stays on a meal', () => {
  assert.equal(isDead({x:2,y:2},{w:5,h:5,body:[{x:1,y:1},{x:2,y:1},{x:2,y:2}],food:{x:2,y:2}}), true);
});
