export function hitsWall(pos, w, h) {
  return pos.x < 0 || pos.y < 0 || pos.x >= w || pos.y >= h;
}
