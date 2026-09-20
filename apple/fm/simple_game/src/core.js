// src/core.js - the barrel of the core units.
// build.sh writes this file. The model never writes an import line.
export { samePos } from './samePos.js';
export { nextHead } from './nextHead.js';
export { turn } from './turn.js';
export { hitsWall } from './hitsWall.js';
export { hitsSelf } from './hitsSelf.js';
export { growOrMove } from './growOrMove.js';
export { freeCells } from './freeCells.js';
export { pickCell } from './pickCell.js';
export { placeFood } from './placeFood.js';
export { createState } from './createState.js';
export { isDead } from './isDead.js';
export { advance } from './advance.js';
export { step } from './step.js';
