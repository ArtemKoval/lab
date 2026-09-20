## SIGNATURE
export function samePos(a, b)

## STYLE
rules

## DEPS
none

## DESCRIPTION
1. a and b are cell objects {x, y} with integer fields.
2. Return true when a.x === b.x and a.y === b.y.
3. Return false in every other case.
4. Change no argument. Call no function.

## EXAMPLES
samePos({x:1,y:2},{x:1,y:2}) -> true
samePos({x:1,y:2},{x:2,y:1}) -> false

## TYPES
a is {x, y}. b is {x, y}. The result is true or false.

## BEHAVIOUR
The result is true only when both fields are equal.

## CASES
1. equal cells: samePos({x:1,y:2},{x:1,y:2}) === true
2. x differs: samePos({x:1,y:2},{x:2,y:2}) === false
3. y differs: samePos({x:1,y:2},{x:1,y:3}) === false
4. both differ: samePos({x:0,y:0},{x:3,y:3}) === false

## DOMAIN
a, b: {x, y} with x, y in [-1..3]

## HINT
a.x === b.x && a.y === b.y

## FALLBACK
export function samePos(a, b) { return a.x === b.x && a.y === b.y; }
