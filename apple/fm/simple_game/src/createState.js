export function createState(w, h) {
  {
    return {
      w: w,
      h: h,
      body: [{ x: 2, y: 1 }, { x: 1, y: 1 }],
      dir: 'right',
      food: { x: 5, y: 5 },
      score: 0,
      over: false
    };
  }
}
