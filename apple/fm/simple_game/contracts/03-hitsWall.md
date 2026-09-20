## SIGNATURE
export function hitsWall(pos, w, h)

## STYLE
rules

## DEPS
none

## DESCRIPTION
1. pos is a cell object {x, y} with integer fields.
2. w and h are positive integers. The grid holds x from 0 to w - 1 and y from 0 to h - 1.
3. Return true when pos.x < 0 || pos.y < 0 || pos.x >= w || pos.y >= h.
4. Return false in every other case.
5. Pure: change no argument. Keep the complexity at 5 or less.

## EXAMPLES
hitsWall({x:0,y:0},4,4) -> false
hitsWall({x:4,y:1},4,4) -> true

## TYPES
pos is {x, y}. w and h are integers. The result is true or false.

## BEHAVIOUR
Cell w - 1 is inside. Cell w is outside.

## CASES
1. inside: hitsWall({x:0,y:0},4,4) === false
2. far corner: hitsWall({x:3,y:3},4,4) === false
3. x past edge: hitsWall({x:4,y:1},4,4) === true
4. y past edge: hitsWall({x:1,y:4},4,4) === true
5. negative x: hitsWall({x:-1,y:1},4,4) === true
6. negative y: hitsWall({x:1,y:-1},4,4) === true

## DOMAIN
pos: {x, y} with x, y in [-2..5]. w, h: 1, 4, 10

## HINT
pos.x < 0 || pos.y < 0 || pos.x >= w || pos.y >= h

## FALLBACK
export function hitsWall(pos, w, h) { return pos.x < 0 || pos.y < 0 || pos.x >= w || pos.y >= h; }
