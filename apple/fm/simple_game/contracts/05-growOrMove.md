## SIGNATURE
export function growOrMove(body, head, ate)

## STYLE
rules

## DEPS
none

## DESCRIPTION
1. body is an array of cells {x, y}. head is a cell {x, y}. ate is a boolean.
2. Return a brand new array. Never change body.
3. When ate is true, return [head, ...body].
4. When ate is false, return [head, ...body.slice(0, -1)].
5. Write no other statement. Pure. Complexity max 5.

## EXAMPLES
growOrMove([{x:1,y:1}],{x:2,y:1},false) -> [{x:2,y:1}]
growOrMove([{x:1,y:1}],{x:2,y:1},true) -> [{x:2,y:1},{x:1,y:1}]

## TYPES
body is an array of {x, y}. head is {x, y}. ate is a boolean. The result is a new array of {x, y}.

## BEHAVIOUR
head goes to index 0. A move without food drops the final cell.
Every expected value is an array. Write assert.deepEqual in every case.

## CASES
1. move: growOrMove([{x:1,y:1}],{x:2,y:1},false) === [{x:2,y:1}]
2. grow: growOrMove([{x:1,y:1}],{x:2,y:1},true) === [{x:2,y:1},{x:1,y:1}]
3. two cells: growOrMove([{x:1,y:1},{x:0,y:1}],{x:2,y:1},false) === [{x:2,y:1},{x:1,y:1}]
4. empty body: growOrMove([],{x:0,y:0},false) === [{x:0,y:0}]
5. long move: growOrMove([{x:1,y:1},{x:0,y:1},{x:0,y:0}],{x:2,y:1},false) === [{x:2,y:1},{x:1,y:1},{x:0,y:1}]

## DOMAIN
body: [], [{x:1,y:1}], [{x:1,y:1},{x:0,y:1}], [{x:1,y:1},{x:0,y:1},{x:0,y:0}]. head: {x:2,y:1}, {x:0,y:0}. ate: true, false

## HINT
ate ? [head, ...body] : [head, ...body.slice(0, -1)]

## FALLBACK
export function growOrMove(body, head, ate) { return ate ? [head, ...body] : [head, ...body.slice(0, -1)]; }
