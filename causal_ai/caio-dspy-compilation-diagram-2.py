#!/usr/bin/env python3
"""
CAIO Diagram: The Compilation Lifecycle
Topic: dspy-compilation
Type: Circular flow (process wheel)
Output: caio-dspy-compilation-diagram-2.png
"""

import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
TAUPE = HexColor('#8A7B6B')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
UMBER = HexColor('#6B4226')

pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-dspy-compilation-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2.pdf'


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 80, 'The DSPy compilation lifecycle')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 110,
        'Six steps in a closed loop. Recompiling against a new model is a configuration change, not an engineering project.')

    # Circular flow with 6 numbered nodes
    cx, cy = W / 2, H / 2 - 30
    orbit_r = 320
    node_r = 78

    steps = [
        ('1', 'Declare', 'Define signatures —\ninput / output types', NAVY),
        ('2', 'Wire', 'Compose modules —\nPredict, CoT, ReAct', SAPPHIRE),
        ('3', 'Measure', 'Define the metric —\nbusiness outcome', EMERALD),
        ('4', 'Compile', 'Run optimizer —\nGEPA, MIPROv2', BURGUNDY),
        ('5', 'Evaluate', 'Score outputs —\ngate to production', AMETHYST),
        ('6', 'Migrate', 'New model —\nrecompile, redeploy', UMBER),
    ]
    n = len(steps)
    positions = []
    for i in range(n):
        ang = math.radians(90 - i * (360 / n))
        x = cx + orbit_r * math.cos(ang)
        y = cy + orbit_r * math.sin(ang)
        positions.append((x, y))

    # Connector lines with arrow tips
    c.setStrokeColor(TAUPE)
    c.setLineWidth(2.5)
    for i in range(n):
        x1, y1 = positions[i]
        x2, y2 = positions[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        d = math.hypot(dx, dy)
        if d < 1e-6:
            continue
        ux, uy = dx / d, dy / d
        sx1, sy1 = x1 + ux * node_r, y1 + uy * node_r
        sx2, sy2 = x2 - ux * node_r, y2 - uy * node_r
        c.line(sx1, sy1, sx2, sy2)
        # Arrow tip
        ah = 14
        aw = 9
        px, py = -uy, ux
        tx1 = sx2 - ux * ah + px * aw
        ty1 = sy2 - uy * ah + py * aw
        tx2 = sx2 - ux * ah - px * aw
        ty2 = sy2 - uy * ah - py * aw
        p = c.beginPath()
        p.moveTo(sx2, sy2)
        p.lineTo(tx1, ty1)
        p.lineTo(tx2, ty2)
        p.close()
        c.setFillColor(TAUPE)
        c.drawPath(p, stroke=0, fill=1)

    # Nodes
    for i, (num, verb, desc, color) in enumerate(steps):
        x, y = positions[i]
        c.setFillColor(color)
        c.circle(x, y, node_r, stroke=0, fill=1)
        # Number inside
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 36)
        c.drawCentredString(x, y - 12, num)
        # Verb below number inside (Ivory)
        c.setFont('Poppins-Light', 14)
        c.drawCentredString(x, y - 36, verb.upper())
        # Description outside, Navy
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 16)
        # Determine label position based on angular position
        ang = math.atan2(y - cy, x - cx)
        ox = math.cos(ang) * (node_r + 20)
        oy = math.sin(ang) * (node_r + 20)
        lx = x + ox
        ly = y + oy
        # text alignment
        cos_v = math.cos(ang)
        for j, line in enumerate(desc.split('\n')):
            if cos_v > 0.3:
                c.drawString(lx, ly - j * 18, line)
                c.setFont('Poppins', 14)
            elif cos_v < -0.3:
                c.drawRightString(lx, ly - j * 18, line)
                c.setFont('Poppins', 14)
            else:
                c.drawCentredString(lx, ly - j * 18 + (24 if oy > 0 else -8), line)
                c.setFont('Poppins', 14)
            c.setFont('Poppins-Bold', 16) if j == 0 else None
        # Reset font for next iteration
        c.setFont('Poppins-Bold', 16)

    # Central label
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(cx, cy + 18, 'COMPILE')
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Light', 18)
    c.drawCentredString(cx, cy - 14, 'not prompt')

    # Footer caption
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 60,
        'The loop runs each time the underlying model changes. The pipeline structure is reused. The prompt is regenerated.')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run([
        'pdftoppm', '-png', '-r', '150', '-singlefile',
        OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f'Rendered: {OUTPUT_PNG}')


if __name__ == '__main__':
    main()
