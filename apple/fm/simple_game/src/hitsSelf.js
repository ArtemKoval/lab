export function hitsSelf(pos, body) {
  const x = pos.x;
  const y = pos.y;
  const len = body.length;
  for (let i = 0; i < len; i++) {
    const c = body[i];
    if (c.x === x && c.y === y) {
      return true;
    }
  }
  return false;
}
