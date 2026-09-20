## GLOSSARY
state is the first game state. tick is a function that takes one state and gives the next state.
render is a function that takes one state and draws it. ms is an integer count of milliseconds.

## STEPS
1. Write the first line function startLoop(state, tick, render, ms) {
2. Declare a variable with let named s and set it to state.
3. Call render(s).
4. Call setInterval(() => { s = tick(s); render(s); }, ms).
5. Write the last line }

## EXAMPLES
The period comes from the parameter. Write the name ms. Write no number.

## SCOPE
Use no global name other than setInterval. Call no function other than setInterval, tick and render.
Write no other statement. Never write a backtick.

## RETURN_CLAUSE
The function returns nothing. The first characters of your answer are function startLoop.
