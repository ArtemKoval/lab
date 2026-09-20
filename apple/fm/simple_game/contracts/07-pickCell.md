## SIGNATURE
export function pickCell(free, rng)

## STYLE
rules

## DEPS
none

## DESCRIPTION
1. free is an array of cells {x, y}. rng takes no argument and gives a number from 0 inclusive to 1 exclusive.
2. Write this line first: if (free.length === 0) return null;
3. Write this line second: const r = rng();
4. Write this line third: const i = Math.floor(r * free.length);
5. Write this line last: return free[i];
6. Write no other statement. Pure. Complexity max 5.

## EXAMPLES
pickCell([],()=>0) -> null
pickCell([{x:0,y:0},{x:1,y:0}],()=>0.99) -> {x:1,y:0}

## TYPES
free is an array of {x, y}. rng is a function. The result is a cell {x, y} or null.

## BEHAVIOUR
rng runs one time at most.

## CASES
1. empty list: pickCell([],()=>0) === null
2. rng zero: pickCell([{x:0,y:0},{x:1,y:0}],()=>0) === {x:0,y:0}
3. rng near one: pickCell([{x:0,y:0},{x:1,y:0}],()=>0.99) === {x:1,y:0}
4. middle of three: pickCell([{x:0,y:0},{x:1,y:0},{x:2,y:0}],()=>0.5) === {x:1,y:0}
5. last of three: pickCell([{x:0,y:0},{x:1,y:0},{x:2,y:0}],()=>0.99) === {x:2,y:0}

## DOMAIN
free: [], [{x:0,y:0},{x:1,y:0}], [{x:0,y:0},{x:1,y:0},{x:2,y:0}]. rng: () => 0, () => 0.34, () => 0.5, () => 0.99

## HINT
if (free.length === 0) return null;

## FALLBACK
export function pickCell(free, rng) {
  if (free.length === 0) return null;
  const r = rng();
  const i = Math.floor(r * free.length);
  return free[i];
}
