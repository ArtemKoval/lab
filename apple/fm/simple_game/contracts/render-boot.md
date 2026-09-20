## GLOSSARY
doc is the browser document. cols and rows are integer counts of grid cells.
cell is the pixel size of one grid cell.
These four names already exist in the file. Do not define them and do not import them:
createState(cols, rows), tick, press(event), startLoop(state, tick, render, ms), drawBoard(ctx, state, cell).

## STEPS
1. Declare const canvas and set it to doc.getElementById('game').
2. Set canvas.width to cols * cell.
3. Set canvas.height to rows * cell.
4. Declare const ctx and set it to canvas.getContext('2d').
5. Call doc.addEventListener('keydown', (e) => press(e)).
6. Declare const draw and set it to (s) => drawBoard(ctx, s, cell).
7. Call startLoop(createState(cols, rows), tick, draw, 120).

## EXAMPLES
The step 5 call gives press the whole event, never the key name alone.
With cols 20 and cell 20 the step 2 line is canvas.width = cols * cell.
The step 7 call always uses the number 120.

## SCOPE
Use no global name. Write no other statement. Never write a backtick.

## RETURN_CLAUSE
The function returns nothing.
