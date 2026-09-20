export function freeCells(occupied, w, h) {
  const grid = Array.from({ length: w * h }, (_, i) => ({ x: i % w, y: Math.floor(i / w) }));
  return grid.filter((c) => !occupied.some((o) => o.x === c.x && o.y === c.y));
}
