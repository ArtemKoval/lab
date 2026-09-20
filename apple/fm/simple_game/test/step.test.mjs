import { test } from 'node:test';
import assert from 'node:assert/strict';
import { step } from '../src/step.js';

const S = {w:3,h:3,body:[{x:2,y:1}],dir:'right',food:{x:2,y:2},score:0};

test('move body', () => {
  assert.deepEqual(step(S,'up',()=>0).body, [{x:2,y:0 }]);
});

test('food stays', () => {
  assert.deepEqual(step(S,'up',()=>0).food, {x:2,y:2});
});

test('eat raises score', () => {
  assert.equal(step(S,'down',()=>0).score, 1);
});

test('eat grows body', () => {
  assert.deepEqual(step(S,'down',()=>0).body, [{x:2,y:2},{x:2,y:1 }]);
});

test('new food cell', () => {
  assert.deepEqual(step(S,'down',()=>0).food, {x:0,y:0});
});

test('wall ends game', () => {
  assert.strictEqual(step(S,null,()=>0).over, true);
});

test('reversal refused', () => {
  assert.strictEqual(step(S,'left',()=>0).dir, 'right');
});

test('turn applied', () => {
  assert.strictEqual(step(S,'up',()=>0).dir, 'up');
});

test('over state kept', () => {
  assert.equal(step({over:true,score:7},'down',()=>0).score, 7);
});
