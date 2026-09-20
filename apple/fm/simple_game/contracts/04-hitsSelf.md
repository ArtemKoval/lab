## SIGNATURE
export function hitsSelf(pos, body)

## STYLE
rules

## DEPS
none

## DESCRIPTION
1. pos is a cell object {x, y}. body is an array of cell objects {x, y}.
2. Compare two cells by the x number and by the y number. Never compare two objects with === and never with Array.prototype.includes.
3. Return true when at least one cell c of body has c.x === pos.x and c.y === pos.y.
4. Return false when no cell of body matches, and return false when body is empty.
5. Return the literal true or the literal false. Never return 1 or 0.
6. Pure: change no argument. Keep the complexity at 5 or less.

## EXAMPLES
hitsSelf({x:1,y:1},[{x:1,y:1}]) -> true
hitsSelf({x:0,y:0},[]) -> false

## TYPES
pos is {x, y}. body is an array of {x, y}. The result is true or false.

## BEHAVIOUR
An empty body gives false.

## CASES
1. only cell: hitsSelf({x:1,y:1},[{x:1,y:1}]) === true
2. first cell: hitsSelf({x:0,y:1},[{x:0,y:1},{x:2,y:1}]) === true
3. last cell: hitsSelf({x:2,y:1},[{x:0,y:1},{x:2,y:1}]) === true
4. miss on x: hitsSelf({x:1,y:1},[{x:0,y:1}]) === false
5. miss on y: hitsSelf({x:0,y:0},[{x:0,y:1}]) === false
6. empty body: hitsSelf({x:0,y:0},[]) === false

## DOMAIN
pos: {x, y} with x, y in [-1..3]. body: [], [{x:1,y:1}], [{x:0,y:1},{x:2,y:1}]

## HINT
body.some((c) => c.x === pos.x && c.y === pos.y)

## FALLBACK
export function hitsSelf(pos, body) { return body.some((c) => c.x === pos.x && c.y === pos.y); }
