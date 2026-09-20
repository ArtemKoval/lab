## SIGNATURE
export function createState(w, h)

## STYLE
rules

## DEPS
none

## DESCRIPTION
1. w and h are positive integers of at least 8.
2. Return one new object literal with exactly these seven fields in this order: w is w, h is h, body is [{x:2,y:1},{x:1,y:1}], dir is 'right', food is {x:5,y:5}, score is 0, over is false.
3. Use no other field. Call no function. Pure. Complexity max 5.

## EXAMPLES
createState(20,20).dir -> 'right'
createState(20,20).body -> [{x:2,y:1},{x:1,y:1}]

## TYPES
w and h are integers. The result is a new object with the fields w, h, body, dir, food, score and over.

## BEHAVIOUR
The start state is fixed. It calls no random function.

## CASES
1. start body: createState(20,20).body === [{x:2,y:1},{x:1,y:1}]
2. start direction: createState(20,20).dir === 'right'
3. start food: createState(20,20).food === {x:5,y:5}
4. start score: createState(20,20).score === 0
5. not over: createState(20,20).over === false
6. grid width: createState(12,9).w === 12
7. grid height: createState(12,9).h === 9

## DOMAIN
w, h: 8, 12, 20

## HINT
{w, h, body: [{x:2,y:1},{x:1,y:1}], dir: 'right', food: {x:5,y:5}, score: 0, over: false}

## FALLBACK
export function createState(w, h) {
  return {w, h, body: [{x:2,y:1},{x:1,y:1}], dir: 'right', food: {x:5,y:5}, score: 0, over: false};
}
