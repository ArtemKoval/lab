## SIGNATURE
export function turn(current, input)

## STYLE
rules

## DEPS
none

## DESCRIPTION
1. current is one of the strings 'up', 'down', 'left', 'right'.
2. input is one of those four strings, or null.
3. Declare a lookup object named OPP in the function with exactly these four pairs: up is 'down', down is 'up', left is 'right', right is 'left'.
4. If OPP[current] === input, return current.
5. If input is 'up' or 'down' or 'left' or 'right', return input.
6. In every other case return current.
7. Pure: change no argument. Keep the complexity at 5 or less.

## EXAMPLES
turn('right','left') -> 'right'
turn('right','up') -> 'up'
turn('up',null) -> 'up'

## TYPES
current is a direction string. input is a direction string or null. The result is a direction string.

## BEHAVIOUR
The function refuses a 180 degree reversal and keeps current.

## CASES
1. turn left: turn('up','left') === 'left'
2. turn right: turn('up','right') === 'right'
3. turn up: turn('left','up') === 'up'
4. reversal from right: turn('right','left') === 'right'
5. reversal from up: turn('up','down') === 'up'
6. reversal from down: turn('down','up') === 'down'
7. no key press: turn('up',null) === 'up'
8. unknown key: turn('up','x') === 'up'

## DOMAIN
current: 'up', 'down', 'left', 'right'. input: those four, null and 'x'

## HINT
if (OPP[current] === input) return current;

## FALLBACK
export function turn(current, input) {
  const OPP = {up:'down',down:'up',left:'right',right:'left'};
  if (OPP[current] === input) return current;
  return OPP[input] ? input : current;
}
