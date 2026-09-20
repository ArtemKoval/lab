export function turn(current, input) {
  const OPP = { up: 'down', down: 'up', left: 'right', right: 'left' };
  if (OPP[current] === input) return current;
  if (['up', 'down', 'left', 'right'].includes(input)) return input;
  return current;
}
