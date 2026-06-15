#!/usr/bin/env python3
"""
CAIO Diagram: Compounding Context Across Model Generations
Topic: caio-context-half-life
Type: Spiral arrangement (Archimedean)
Output: caio-context-half-life-diagram-2.png
"""

import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
UMBER = HexColor('#6B4226')
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')

FD = '/usr/share/fonts/truetype/google-fonts/'
pdfmetrics.registerFont(TTFont('Poppins', FD + 'Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', FD + 'Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', FD + 'Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', FD + 'Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Italic', FD + 'Poppins-Italic.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-context-half-life-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'

CX, CY = 800, 535
A, B = 55.0, 36.5            # spiral: r equals A plus B times theta
T0, T1 = 0.55 * math.pi, 3.35 * math.pi
NODE_R = 36
LABEL_GAP = 94

NODES = [
    ('Prompt + instruction library', '2023'),
    ('Retrieval corpus v1', '2023'),
    ('Evaluation suite', '2024'),
    ('Routing + gateway policies', '2024'),
    ('Institutional memory store', '2025'),
    ('Observability + trace archive', '2025'),
    ('Governance + autonomy rules', '2026'),
    ('Portable context graph', '2026'),
]
NODE_COLORS = [NAVY, SAPPHIRE, EMERALD, BURGUNDY, AMETHYST, UMBER, TEAL, GRAPHITE]

# Per-node manual label nudges (dx, dy) applied after radial placement
NUDGE = {5: (0, 10)}
# Nodes whose labels sit inside the spiral (left-anchored beside the node)
INSIDE_RIGHT = {0}


def spiral_point(theta):
    r = A + B * theta
    return CX + r * math.cos(theta), CY + r * math.sin(theta)


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W / 2, 1128, 'Compounding Context Across Model Generations')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(W / 2, 1094,
                        'Model generations rotate — context assets accumulate along the curve')

    # Spiral path
    c.setStrokeColor(TAUPE)
    c.setLineWidth(2.5)
    p = c.beginPath()
    steps = 480
    x0, y0 = spiral_point(T0)
    p.moveTo(x0, y0)
    for i in range(1, steps + 1):
        t = T0 + (T1 - T0) * i / steps
        x, y = spiral_point(t)
        p.lineTo(x, y)
    c.drawPath(p, stroke=1, fill=0)

    # Origin dot
    c.setFillColor(NAVY)
    c.setStrokeColor(WHITE)
    c.setLineWidth(2)
    c.circle(CX, CY, 14, stroke=1, fill=1)

    # Nodes and labels
    step = (3.25 * math.pi - 0.8 * math.pi) / 7.0
    for i, ((name, era), col) in enumerate(zip(NODES, NODE_COLORS)):
        theta = 0.8 * math.pi + i * step
        r = A + B * theta
        nx, ny = CX + r * math.cos(theta), CY + r * math.sin(theta)

        c.setFillColor(col)
        c.setStrokeColor(WHITE)
        c.setLineWidth(3)
        c.circle(nx, ny, NODE_R, stroke=1, fill=1)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 19)
        c.drawCentredString(nx, ny - 6.5, str(i + 1))

        lx = CX + (r + LABEL_GAP) * math.cos(theta)
        ly = CY + (r + LABEL_GAP) * math.sin(theta)
        dx, dy = NUDGE.get(i, (0, 0))
        lx, ly = lx + dx, ly + dy

        cosv = math.cos(theta)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 16)
        if i in INSIDE_RIGHT:
            ix, iy = nx + 48, ny - 44
            c.drawString(ix, iy, name)
            c.setFillColor(GRAPHITE)
            c.setFont('Poppins-Light', 12)
            c.drawString(ix, iy - 19, era)
        elif cosv > 0.25:
            c.drawString(lx, ly, name)
            c.setFillColor(GRAPHITE)
            c.setFont('Poppins-Light', 12)
            c.drawString(lx, ly - 19, era)
        elif cosv < -0.25:
            c.drawRightString(lx, ly, name)
            c.setFillColor(GRAPHITE)
            c.setFont('Poppins-Light', 12)
            c.drawRightString(lx, ly - 19, era)
        else:
            yoff = 6 if math.sin(theta) > 0 else -14
            c.drawCentredString(lx, ly + yoff, name)
            c.setFillColor(GRAPHITE)
            c.setFont('Poppins-Light', 12)
            c.drawCentredString(lx, ly + yoff - 19, era)


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                    OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    print(f'Rendered: {OUTPUT_PNG}')


if __name__ == '__main__':
    main()
