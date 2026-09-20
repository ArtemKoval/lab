## SIGNATURE
export function advance(state, dir, head, rng)

## STYLE
skeleton

## DEPS
samePos(a, b), growOrMove(body, head, ate), placeFood(occupied, w, h, rng)

## DESCRIPTION
Fill each hole of SKELETON with the text under HOLES. Copy each ternary in full. Pure: build a new state and change no argument. Complexity max 5. Never add a fifth parameter. A full board gives the food value null, and the new state is then over.

## EXAMPLES
advance(S,'up',{x:2,y:0},()=>0).score -> 0
advance(S,'down',{x:2,y:2},()=>0).score -> 1

## TYPES
state holds w, h, body, dir, food and score. dir is a direction string. head is {x, y}. rng gives a number from 0 to 1. The result is a new state with the key over.

## BEHAVIOUR
Write this line one time after the imports, then use S in every case:
const S = {w:3,h:3,body:[{x:2,y:1}],dir:'right',food:{x:2,y:2},score:0};
Never change S. The snake eats when head is on the food. A board with no free cell gives the food value null, and that state is over.

## CASES
1. move body: advance(S,'up',{x:2,y:0},()=>0).body === [{x:2,y:0}]
2. move keeps food: advance(S,'up',{x:2,y:0},()=>0).food === {x:2,y:2}
3. move keeps score: advance(S,'up',{x:2,y:0},()=>0).score === 0
4. eat grows body: advance(S,'down',{x:2,y:2},()=>0).body === [{x:2,y:2},{x:2,y:1}]
5. eat raises score: advance(S,'down',{x:2,y:2},()=>0).score === 1
6. eat places food: advance(S,'down',{x:2,y:2},()=>0).food === {x:0,y:0}
7. dir is copied: advance(S,'up',{x:2,y:0},()=>0).dir === 'up'
8. a full board ends the game: advance({w:1,h:2,body:[{x:0,y:1}],dir:'up',food:{x:0,y:0},score:0},'up',{x:0,y:0},()=>0).over === true
9. a free board keeps the game: advance(S,'up',{x:2,y:0},()=>0).over === false

## DOMAIN
state: S and the state of the case 8. dir: 'up', 'down'. head: {x:2,y:0}, {x:2,y:2}, {x:0,y:0}. rng: () => 0, () => 0.99

## HINT
const ate = samePos(head, state.food);

## SKELETON
export function advance(state, dir, head, rng) {
  const ate = ???;
  const body = growOrMove(state.body, head, ate);
  const food = ???;
  const score = ???;
  const over = ???;
  return { ...state, dir, body, food, score, over };
}

## HOLES
Hole 1 is: samePos(head, state.food)
Hole 2 is: ate ? placeFood(body, state.w, state.h, rng) : state.food
Hole 3 is: ate ? state.score + 1 : state.score
Hole 4 is: food === null

## FALLBACK
export function advance(state, dir, head, rng) {
  const ate = samePos(head, state.food);
  const body = growOrMove(state.body, head, ate);
  const food = ate ? placeFood(body, state.w, state.h, rng) : state.food;
  const score = ate ? state.score + 1 : state.score;
  const over = food === null;
  return { ...state, dir, body, food, score, over };
}
