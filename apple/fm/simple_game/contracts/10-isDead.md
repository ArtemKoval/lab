## SIGNATURE
export function isDead(head, state)

## STYLE
skeleton

## DEPS
hitsWall(pos, w, h), hitsSelf(pos, body), samePos(a, b), growOrMove(body, head, ate)

## DESCRIPTION
Fill each hole of SKELETON with the text under HOLES. Copy every other character as it is written. The head is dead when it leaves the grid or when it meets a body cell that stays. Pure. Complexity max 5.

## EXAMPLES
isDead({x:-1,y:0},D) -> true
isDead({x:2,y:2},D) -> false

## TYPES
head is {x, y}. state holds w, h, body and food. The result is true or false.

## BEHAVIOUR
Write this line one time after the imports, then use D in every case:
const D = {w:5,h:5,body:[{x:1,y:1},{x:2,y:1},{x:2,y:2}],food:{x:4,y:4}};
Never change D. The last cell of body is the tail. The tail leaves its cell on the same tick, so the head may enter the tail cell. The tail stays when the head lands on the food.

## CASES
1. wall on x: isDead({x:-1,y:0},D) === true
2. wall on y: isDead({x:0,y:5},D) === true
3. body cell: isDead({x:2,y:1},D) === true
4. free cell: isDead({x:3,y:3},D) === false
5. tail cell is free: isDead({x:2,y:2},D) === false
6. tail stays on a meal: isDead({x:2,y:2},{w:5,h:5,body:[{x:1,y:1},{x:2,y:1},{x:2,y:2}],food:{x:2,y:2}}) === true

## DOMAIN
head: {x, y} with x, y in [-1..5]. state: D, and the state of the case 6.

## HINT
growOrMove(state.body, head, ate).slice(1)

## SKELETON
export function isDead(head, state) {
  const ate = ???;
  const rest = ???;
  return hitsWall(head, state.w, state.h) || hitsSelf(head, rest);
}

## HOLES
Hole 1 is: samePos(head, state.food)
Hole 2 is: growOrMove(state.body, head, ate).slice(1)

## FALLBACK
export function isDead(head, state) {
  const ate = samePos(head, state.food);
  const rest = growOrMove(state.body, head, ate).slice(1);
  return hitsWall(head, state.w, state.h) || hitsSelf(head, rest);
}
