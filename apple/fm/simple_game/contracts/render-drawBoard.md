## GLOSSARY
ctx is a canvas 2d context. state holds w, h, body, food, score and over.
cell is the pixel size of one grid cell. state.body is an array of cells {x, y}.
state.food is a cell {x, y}, or it is null when the board holds no free cell.
state.score is an integer. state.over is true or false.

## STEPS
1. Set ctx.fillStyle to '#111111'.
2. Call ctx.fillRect(0, 0, state.w * cell, state.h * cell).
3. Set ctx.fillStyle to '#ee3333'.
4. If state.food is not null, call ctx.fillRect(state.food.x * cell, state.food.y * cell, cell, cell).
5. Set ctx.fillStyle to '#33ee66'.
6. Call state.body.forEach((c) => ctx.fillRect(c.x * cell, c.y * cell, cell, cell)).
7. Set ctx.fillStyle to '#eeeeee'.
8. Set ctx.font to '16px monospace'.
9. Call ctx.fillText('Score: ' + state.score, 8, 16).
10. If state.over is true, call ctx.fillText('GAME OVER', 8, 36).
11. If state.food is null, call ctx.fillText('YOU WIN', 8, 56).

## EXAMPLES
With cell 20 and state.w 20 the step 2 call is ctx.fillRect(0, 0, 400, 400).
With food {x:5,y:5} and cell 20 the step 4 call is ctx.fillRect(100, 100, 20, 20).

## SCOPE
The step 4 guard matters. A full board gives state.food the value null, and a read
of state.food.x then throws inside the loop and the board stops.
Use no global name. Call no function other than the ctx methods and forEach.
Never write a backtick. Join two strings with the + operator only.

## RETURN_CLAUSE
The function returns nothing.
