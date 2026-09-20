import { freeCells } from './freeCells.js';
import { pickCell } from './pickCell.js';
export function placeFood(occupied, w, h, rng) {
  const free = freeCells(occupied, w, h);
  return pickCell(free, rng);
}
