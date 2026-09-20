## SIGNATURE
export function step(state, input, rng)

## STYLE
skeleton

## DEPS
turn(current, input), nextHead(pos, dir), isDead(head, state), advance(state, dir, head, rng)

## DESCRIPTION
Fill each hole of SKELETON with the text under HOLES. Copy every other character as it is written. Pure: build a new state and change no argument. Complexity max 5.

## EXAMPLES
step(S,'left',()=>0).dir -> 'right'
step(S,'down',()=>0).score -> 1

## TYPES
state holds w, h, body, dir, food, score and over. input is a direction string or null. rng gives a number from 0 to 1. The result is a new state.

## BEHAVIOUR
Write this line one time after the imports, then use S in every case:
const S = {w:3,h:3,body:[{x:2,y:1}],dir:'right',food:{x:2,y:2},score:0};
Never change S. input null means no key press.

## CASES
1. move body: step(S,'up',()=>0).body === [{x:2,y:0}]
2. food stays: step(S,'up',()=>0).food === {x:2,y:2}
3. eat raises score: step(S,'down',()=>0).score === 1
4. eat grows body: step(S,'down',()=>0).body === [{x:2,y:2},{x:2,y:1}]
5. new food cell: step(S,'down',()=>0).food === {x:0,y:0}
6. wall ends game: step(S,null,()=>0).over === true
7. reversal refused: step(S,'left',()=>0).dir === 'right'
8. turn applied: step(S,'up',()=>0).dir === 'up'
9. over state kept: step({over:true,score:7},'down',()=>0).score === 7

## DOMAIN
state: S. input: null, 'up', 'down', 'left', 'right'. rng: () => 0

## HINT
const dir = turn(state.dir, input);

## SKELETON
export function step(state, input, rng) {
  if (state.over) return state;
  const dir = ???;
  const head = ???;
  if (isDead(head, state)) return { ...state, dir, over: true };
  return advance(state, dir, head, rng);
}

## HOLES
Hole 1 is: turn(state.dir, input)
Hole 2 is: nextHead(state.body[0], dir)

## FALLBACK
export function step(state, input, rng) {
  if (state.over) return state;
  const dir = turn(state.dir, input);
  const head = nextHead(state.body[0], dir);
  if (isDead(head, state)) return { ...state, dir, over: true };
  return advance(state, dir, head, rng);
}
