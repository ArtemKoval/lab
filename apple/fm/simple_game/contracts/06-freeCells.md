## SIGNATURE
export function freeCells(occupied, w, h)

## STYLE
rules

## DEPS
none

## DESCRIPTION
1. occupied is an array of cells {x, y}. w and h are positive integers.
2. Declare const grid with this literal expression: Array.from({length: w * h}, (_, i) => ({x: i % w, y: Math.floor(i / w)}))
3. Return this literal expression: grid.filter((c) => !occupied.some((o) => o.x === c.x && o.y === c.y))
4. Write no Set. Write no Map. Write no includes. Write no indexOf. Write no for loop. Write no if statement.
5. The result is an array of cell objects {x, y}. It never holds a number. The order is row by row, x rises fastest.

## EXAMPLES
freeCells([],2,1) -> [{x:0,y:0},{x:1,y:0}]
freeCells([{x:0,y:0}],2,1) -> [{x:1,y:0}]

## TYPES
occupied is an array of {x, y}. w and h are integers. The result is an array of {x, y}.

## BEHAVIOUR
A full grid gives the empty array.

## CASES
1. none taken: freeCells([],2,1) === [{x:0,y:0},{x:1,y:0}]
2. one taken: freeCells([{x:0,y:0}],2,1) === [{x:1,y:0}]
3. full grid: freeCells([{x:0,y:0},{x:1,y:0}],2,1) === []
4. tall grid: freeCells([],1,2) === [{x:0,y:0},{x:0,y:1}]
5. gap in a row: freeCells([{x:1,y:0}],3,1) === [{x:0,y:0},{x:2,y:0}]

## DOMAIN
occupied: [], [{x:0,y:0}], [{x:1,y:0}]. w, h: (2,1), (3,1), (1,2)

## HINT
return grid.filter((c) => !occupied.some((o) => o.x === c.x && o.y === c.y));

## FALLBACK
export function freeCells(occupied, w, h) {
  return Array.from({length: w * h}, (_, i) => ({x: i % w, y: Math.floor(i / w)})).filter((c) => !occupied.some((o) => o.x === c.x && o.y === c.y));
}
