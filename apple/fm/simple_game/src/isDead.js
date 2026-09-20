import { hitsWall } from './hitsWall.js';
import { hitsSelf } from './hitsSelf.js';
import { samePos } from './samePos.js';
import { growOrMove } from './growOrMove.js';
export function isDead(head, state) {
  const ate = samePos(head, state.food);
  const rest = growOrMove(state.body, head, ate).slice(1);
  return hitsWall(head, state.w, state.h) || hitsSelf(head, rest);
}
