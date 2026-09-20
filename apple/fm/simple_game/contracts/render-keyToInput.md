## GLOSSARY
key is a string. It is the key name of a keyboard event.

## STEPS
1. Write the first line function keyToInput(key) {
2. Declare a constant object named KEYS with exactly these twelve pairs:
   'ArrowUp': 'up', 'ArrowDown': 'down', 'ArrowLeft': 'left', 'ArrowRight': 'right',
   'w': 'up', 's': 'down', 'a': 'left', 'd': 'right',
   'W': 'up', 'S': 'down', 'A': 'left', 'D': 'right'.
3. Return this exact expression: KEYS[key] || null
4. Write the last line }

## EXAMPLES
keyToInput('ArrowUp') -> 'up'
keyToInput('d') -> 'right'
keyToInput('D') -> 'right'
keyToInput('Enter') -> null

## SCOPE
The upper case pairs matter. A browser gives 'W' when the caps lock is on or when
the shift key is down, and a map of the lower case letters alone leaves that key dead.
Use no global name. Write no if statement. Use the object KEYS.
Write no other statement. Never write a backtick.

## RETURN_CLAUSE
The function returns a direction string or null.
The first characters of your answer are function keyToInput.
