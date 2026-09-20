import { test } from 'node:test';
import assert from 'node:assert/strict';
import { hitsSelf } from '../src/hitsSelf.js';

test('only cell', () => {
  assert.equal(hitsSelf({ x: 1, y: 1 }, [{ x: 1, y: 1 }]), true);
});

test('first cell', () => {
  assert.equal(hitsSelf({ x: 0, y: 1 }, [{ x: 0, y: 1 }, { x: 2, y: 1 }]), true);
});

test('last cell', () => {
  assert.equal(hitsSelf({ x: 2, y: 1 }, [{ x: 0, y: 1 }, { x: 2, y: 1 }]), true);
});

test('miss on x', () => {
  assert.equal(hitsSelf({ x: 1, y: 1 }, [{ x: 0, y: 1 }]), false);
});

test('miss on y', () => {
  assert.equal(hitsSelf({ x: 0, y: 0 }, [{ x: 0, y: 1 }]), false);
});

test('empty body', () => {
  assert.equal(hitsSelf({ x: 0, y: 0 }, []), false);
});
