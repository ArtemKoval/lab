## GLOSSARY
state is the first game state. tick is a function that takes one state and gives the next state.
render is a function that takes one state and draws it. ms is an integer count of milliseconds.

## STEPS
1. Write the first line function startLoop(state, tick, render, ms) {
2. Declare a variable with let named s and set it to state.
3. Call render(s).
4. Declare a variable with let named id and set it to this expression: setInterval(() => { s = tick(s); render(s); if (s.over) { clearInterval(id); } }, ms)
5. Write the last line }

## EXAMPLES
The period comes from the parameter. Write the name ms. Write no number.
When the state the tick returns has over true, the interval clears itself on that same tick.

## SCOPE
Use no global name other than setInterval and clearInterval. Call no function other than setInterval, clearInterval, tick and render.
Write no other statement. Never write a backtick.

## RETURN_CLAUSE
The function returns nothing. The first characters of your answer are function startLoop.
