#!/usr/bin/env python3
"""
CAIO Diagram: The Optimization Search Curve
Topic: caio-budgeted-search
Type: Spiral arrangement (Archimedean-style spiral with iteration nodes)
Output: caio-budgeted-search-diagram-1.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

# --- Palette (CAIO standard) ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
MUSTARD = HexColor('#C4952A')
BRICK = HexColor('#A04A2A')
TAUPE = HexColor('#8A7B6B')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-budgeted-search-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1.pdf'


def lerp_color(c1, c2, t):
    return Color(c1.red + (c2.red - c1.red) * t,
                 c1.green + (c2.green - c1.green) * t,
                 c1.blue + (c2.blue - c1.blue) * t)


def grad(t):
    # Brick (early) to Mustard (mid) to Emerald (late)
    if t < 0.5:
        return lerp_color(BRICK, MUSTARD, t / 0.5)
    return lerp_color(MUSTARD, EMERALD, (t - 0.5) / 0.5)


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title + subtitle
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 31)
    c.drawCentredString(W / 2, H - 78, 'The Optimization Search Curve')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 110,
                        'Each loop is one iteration of generate, evaluate, select. Early runs buy large gains; later runs flatten.')

    cx, cy = 760, 520
    r0, R = 26, 430
    turns = 3.0
    N = 11  # iteration nodes

    # Continuous spiral path (Taupe) — radius grows concavely (gain per loop shrinks)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(3)
    p = c.beginPath()
    steps = 600
    for i in range(steps + 1):
        t = i / steps
        rad = r0 + (R - r0) * (t ** 0.5)
        ang = math.radians(150) + turns * 2 * math.pi * t
        x = cx + rad * math.cos(ang)
        y = cy + rad * math.sin(ang)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    c.drawPath(p, stroke=1, fill=0)

    # Iteration nodes
    node_positions = []
    for k in range(N):
        t = k / (N - 1)
        rad = r0 + (R - r0) * (t ** 0.5)
        ang = math.radians(150) + turns * 2 * math.pi * t
        x = cx + rad * math.cos(ang)
        y = cy + rad * math.sin(ang)
        node_positions.append((x, y, ang, t))
        nr = 17 if 0 < k < N - 1 else 22
        c.setFillColor(grad(t))
        c.circle(x, y, nr, stroke=1, fill=1)
        c.setStrokeColor(HexColor('#FFFFFF'))
        c.setLineWidth(2.5)
        c.circle(x, y, nr, stroke=1, fill=0)

    # Center marker label "Seed prompt"
    x0, y0, _, _ = node_positions[0]
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 12)
    c.drawCentredString(x0, y0 - 4, 'S0')
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    c.drawString(x0 + 30, y0 - 5, 'Seed prompt')

    # Outermost node: open emphasis ring + plateau label
    xe, ye, ange, _ = node_positions[-1]
    c.setStrokeColor(EMERALD)
    c.setLineWidth(2.5)
    c.circle(xe, ye, 36, stroke=1, fill=0)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 12)
    c.drawCentredString(xe, ye - 4, 'Sn')

    # Quadrant-aware label for the plateau node
    lx = xe + 46 * math.cos(ange)
    ly = ye + 46 * math.sin(ange)
    c.setFillColor(EMERALD)
    c.setFont('Poppins-Bold', 15)
    cosv = math.cos(ange)
    txt1 = 'Frontier reached'
    txt2 = 'further runs buy noise'
    if cosv > 0.3:
        c.drawString(lx, ly + 6, txt1)
        c.setFont('Poppins', 13)
        c.setFillColor(GRAPHITE)
        c.drawString(lx, ly - 12, txt2)
    elif cosv < -0.3:
        c.drawRightString(lx, ly + 6, txt1)
        c.setFont('Poppins', 13)
        c.setFillColor(GRAPHITE)
        c.drawRightString(lx, ly - 12, txt2)
    else:
        c.drawCentredString(lx, ly + 6, txt1)
        c.setFont('Poppins', 13)
        c.setFillColor(GRAPHITE)
        c.drawCentredString(lx, ly - 12, txt2)

    # Legend (circular markers only) bottom-left
    lx0, ly0 = 130, 250
    legend = [
        (BRICK, 'Early loops', 'largest quality gains'),
        (MUSTARD, 'Middle loops', 'gains shrink each pass'),
        (EMERALD, 'Late loops', 'plateau \u2014 set a stopping rule'),
    ]
    c.setFont('Poppins-Medium', 15)
    for i, (col, label, sub) in enumerate(legend):
        yy = ly0 - i * 58
        c.setFillColor(col)
        c.circle(lx0, yy, 13, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 16)
        c.drawString(lx0 + 28, yy + 3, label)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 13)
        c.drawString(lx0 + 28, yy - 16, sub)

    # Bottom caption
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 14)
    c.drawCentredString(W / 2, 40,
                        'Optimization is a budgeted search: spend where the curve still climbs, stop where it flattens.')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    import subprocess
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                    OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    print(f'Rendered: {OUTPUT_PNG}')


if __name__ == '__main__':
    main()
