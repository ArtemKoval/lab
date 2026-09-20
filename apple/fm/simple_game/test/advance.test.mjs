import { test } from 'node:test';
import assert from 'node:assert/strict';
import { advance } from '../src/advance.js';

const S = {w:3,h:3,body:[{x:2,y:1}],dir:'right',food:{x:2,y:2},score:0};

test('move body', () => {
  assert.deepEqual(advance(S,'up',{x:2,y:0},()=>0).body, [{x:2,y:0 }]);
});

test('move keeps food', () => {
  assert.deepEqual(advance(S,'up',{x:2,y:0},()=>0).food, {x:2,y:2});
});

test('move keeps score', () => {
  assert.deepEqual(advance(S,'up',{x:2,y:0},()=>0).score, 0);
});

test('eat grows body', () => {
  assert.deepEqual(advance(S,'down',{x:2,y:2},()=>0).body, [{x:2,y:2},{x:2,y:1 }]);
});

test('eat raises score', () => {
  assert.deepEqual(advance(S,'down',{x:2,y:2},()=>0).score, 1);
});

test('eat places food', () => {
  assert.deepEqual(advance(S,'down',{x:2,y:2},()=>0).food, {x:0,y:0});
});

test('dir is copied', () => {
  assert.equal(advance(S,'up',{x:2,y:0},()=>0).dir, 'up');
});

test('a full board ends the game', () => {
  assert.deepEqual(advance({w:1,h:2,body:[{x:0,y:1}],dir:'up',food:{x:0,y:0},score:0},'up',{x:0,y:0},()=>0).over, true);
});

test('a free board keeps the game', () => {
  assert.deepEqual(advance(S,'up',{x:2,y:0},()=>0).over, false);
});
