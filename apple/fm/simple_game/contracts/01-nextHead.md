## SIGNATURE
export function nextHead(pos, dir)

## STYLE
rules

## DEPS
none

## DESCRIPTION
1. pos is a cell object {x, y} with integer fields.
2. dir is one of the strings 'up', 'down', 'left', 'right'.
3. Declare a lookup object named STEP in the function with exactly these four pairs: up is {x:0,y:-1}, down is {x:0,y:1}, left is {x:-1,y:0}, right is {x:1,y:0}.
4. Return the new object {x: pos.x + STEP[dir].x, y: pos.y + STEP[dir].y}.
5. Pure: change pos never. Keep the complexity at 5 or less.

## EXAMPLES
nextHead({x:2,y:2},'right') -> {x:3,y:2}
nextHead({x:0,y:0},'left') -> {x:-1,y:0}

## TYPES
pos is {x, y}. dir is a direction string. The result is a new {x, y}.

## BEHAVIOUR
y falls by one for 'up'. y rises by one for 'down'.

## CASES
1. right: nextHead({x:2,y:2},'right') === {x:3,y:2}
2. left: nextHead({x:2,y:2},'left') === {x:1,y:2}
3. up: nextHead({x:2,y:2},'up') === {x:2,y:1}
4. down: nextHead({x:2,y:2},'down') === {x:2,y:3}
5. negative x: nextHead({x:0,y:0},'left') === {x:-1,y:0}
6. offset cell: nextHead({x:3,y:1},'down') === {x:3,y:2}

## DOMAIN
pos: {x, y} with x, y in [-1..3]. dir: 'up', 'down', 'left', 'right'

## HINT
{x: pos.x + STEP[dir].x, y: pos.y + STEP[dir].y}

## FALLBACK
export function nextHead(pos, dir) {
  const STEP = {up:{x:0,y:-1},down:{x:0,y:1},left:{x:-1,y:0},right:{x:1,y:0}};
  return {x: pos.x + STEP[dir].x, y: pos.y + STEP[dir].y};
}
