import { test } from 'node:test';
import assert from 'node:assert/strict';
import { growOrMove } from '../src/growOrMove.js';

test('move', () => {
  assert.deepEqual(growOrMove([{x:1,y:1}],{x:2,y:1},false), [{x:2,y:1 }]);
});

test('grow', () => {
  assert.deepEqual(growOrMove([{x:1,y:1}],{x:2,y:1},true), [{x:2,y:1},{x:1,y:1 }]);
});

test('two cells', () => {
  assert.deepEqual(growOrMove([{x:1,y:1},{x:0,y:1}],{x:2,y:1},false), [{x:2,y:1},{x:1,y:1 }]);
});

test('empty body', () => {
  assert.deepEqual(growOrMove([],{x:0,y:0},false), [{x:0,y:0 }]);
});

test('long move', () => {
  assert.deepEqual(growOrMove([{x:1,y:1},{x:0,y:1},{x:0,y:0}],{x:2,y:1},false), [{x:2,y:1},{x:1,y:1},{x:0,y:1 }]);
});
