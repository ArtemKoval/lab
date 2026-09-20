import { test } from 'node:test';
import assert from 'node:assert/strict';
import { placeFood } from '../src/placeFood.js';

test('first free cell', () => {
  assert.deepEqual(placeFood([{x:0,y:0}],2,2,()=>0), {x:1,y:0});
});

test('last free cell', () => {
  assert.deepEqual(placeFood([{x:0,y:0}],2,2,()=>0.99), {x:1,y:1});
});

test('full grid', () => {
  assert.strictEqual(placeFood([{x:0,y:0},{x:1,y:0},{x:0,y:1},{x:1,y:1}],2,2,()=>0), null);
});

test('none taken', () => {
  assert.deepEqual(placeFood([],2,2,()=>0), {x:0,y:0});
});

test('tall grid', () => {
  assert.deepEqual(placeFood([],1,2,()=>0.99), {x:0,y:1});
});

test('middle cell', () => {
  assert.deepEqual(placeFood([{x:0,y:0}],3,1,()=>0.5), {x:2,y:0});
});
