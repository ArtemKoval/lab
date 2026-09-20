## SIGNATURE
export function placeFood(occupied, w, h, rng)

## STYLE
skeleton

## DEPS
freeCells(occupied, w, h), pickCell(free, rng)

## DESCRIPTION
Fill each hole of SKELETON with the text under HOLES. Call freeCells one time and pickCell one time. Pure. Complexity max 5. Never add a fifth parameter.

## EXAMPLES
placeFood([],1,2,()=>0) -> {x:0,y:0}
placeFood([{x:0,y:0}],2,2,()=>0) -> {x:1,y:0}

## TYPES
occupied is an array of {x, y}. w and h are integers. rng gives a number from 0 to 1. The result is a cell {x, y} or null.

## BEHAVIOUR
A full grid gives null. The free cells come row by row, x rises fastest.

## CASES
1. first free cell: placeFood([{x:0,y:0}],2,2,()=>0) === {x:1,y:0}
2. last free cell: placeFood([{x:0,y:0}],2,2,()=>0.99) === {x:1,y:1}
3. full grid: placeFood([{x:0,y:0},{x:1,y:0},{x:0,y:1},{x:1,y:1}],2,2,()=>0) === null
4. none taken: placeFood([],2,2,()=>0) === {x:0,y:0}
5. tall grid: placeFood([],1,2,()=>0.99) === {x:0,y:1}
6. middle cell: placeFood([{x:0,y:0}],3,1,()=>0.5) === {x:2,y:0}

## DOMAIN
occupied: [], [{x:0,y:0}]. w, h: (2,2), (3,1), (1,2). rng: () => 0, () => 0.99

## HINT
pickCell(freeCells(occupied, w, h), rng)

## SKELETON
export function placeFood(occupied, w, h, rng) {
  const free = ???;
  return ???;
}

## HOLES
Hole 1 is: freeCells(occupied, w, h)
Hole 2 is: pickCell(free, rng)

## FALLBACK
export function placeFood(occupied, w, h, rng) {
  const free = freeCells(occupied, w, h);
  return pickCell(free, rng);
}
