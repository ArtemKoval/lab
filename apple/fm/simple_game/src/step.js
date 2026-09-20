import { turn } from './turn.js';
import { nextHead } from './nextHead.js';
import { isDead } from './isDead.js';
import { advance } from './advance.js';
export function step(state, input, rng) {
  if (state.over) return state;
  const dir = turn(state.dir, input);
  const head = nextHead(state.body[0], dir);
  if (isDead(head, state)) return { ...state, dir, over: true };
  return advance(state, dir, head, rng);
}
