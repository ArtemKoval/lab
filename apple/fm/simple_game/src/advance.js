import { samePos } from './samePos.js';
import { growOrMove } from './growOrMove.js';
import { placeFood } from './placeFood.js';
export function advance(state, dir, head, rng) {
  const ate = samePos(head, state.food);
  const body = growOrMove(state.body, head, ate);
  const food = ate ? placeFood(body, state.w, state.h, rng) : state.food;
  const score = ate ? state.score + 1 : state.score;
  const over = food === null;
  return { ...state, dir, body, food, score, over };
}
