export function nextHead(pos, dir) {
  const STEP = { up: { x: 0, y: -1 }, down: { x: 0, y: 1 }, left: { x: -1, y: 0 }, right: { x: 1, y: 0 } };
  return { x: pos.x + STEP[dir].x, y: pos.y + STEP[dir].y };
}
