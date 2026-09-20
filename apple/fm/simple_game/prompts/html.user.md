Write one HTML5 document.

It must contain exactly these elements in this order:
1. <!DOCTYPE html>
2. <html lang="en">
3. <head> with <meta charset="utf-8">, <title>Snake</title>, and a <style> block with two rules. The first rule is for body and it sets background to #111, color to #eee, font-family to monospace and text-align to center. The second rule uses the selector #game and it sets border to 2px solid #555, display to block and margin to 0 auto. Write no border in the body rule.
4. <body> with <h1>Snake</h1>, then <canvas id="game" width="400" height="400"></canvas>, then <p>Arrow keys or WASD</p>, then <script type="module" src="game.js"></script>.
5. </body> and </html>.

The board is painted in the same near black as the page, so the canvas rule is the
only thing that shows the player where the walls are. Write no JavaScript other than
the script tag.
