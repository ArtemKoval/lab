#!/usr/bin/env python3
"""
CAIO Diagram: Naive Prompt vs Engineered Prompt
Topic: caio-prompt-system-moat
Type: Radar overlay (two polygons on a radial grid)
Output: caio-prompt-system-moat-diagram-3.png
"""

import os
import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from PIL import Image

# --- Palette (CAIO standard) ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')

FONT_DIR = '/usr/share/fonts/truetype/google-fonts'
pdfmetrics.registerFont(TTFont('Poppins', FONT_DIR + '/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', FONT_DIR + '/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', FONT_DIR + '/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', FONT_DIR + '/Poppins-Light.ttf'))

W, H = 1600, 1200
HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PNG = os.path.join(HERE, 'caio-prompt-system-moat-diagram-3.png')
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'

AXES = [
    'Brand Fidelity',
    'Visual Consistency',
    'First-Pass Usability',
    'Compositional Control',
    'Scale Readiness',
    'Revision Efficiency',
]
NAIVE = [0.25, 0.20, 0.30, 0.25, 0.18, 0.22]
ENGINEERED = [0.90, 0.92, 0.82, 0.88, 0.90, 0.85]


def polygon_points(cx, cy, maxr, values):
    pts = []
    for i, v in enumerate(values):
        a = math.radians(90 - 60 * i)
        pts.append((cx + maxr * v * math.cos(a), cy + maxr * v * math.sin(a)))
    return pts


def fill_polygon(c, pts, color, alpha):
    c.setFillColor(color)
    c.setFillAlpha(alpha)
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.setFillAlpha(1.0)


def stroke_polygon(c, pts, color, width):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.drawPath(p, stroke=1, fill=0)


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 36)
    c.drawCentredString(W / 2, H - 78, 'Naive Prompt vs Engineered Prompt')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 18)
    c.drawCentredString(W / 2, H - 112,
                        'Illustrative capability profile across six production dimensions')

    cx, cy = 800, 520
    maxr = 318

    # Grid rings (concentric circles, stroke only)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(1.0)
    for lvl in (0.25, 0.5, 0.75, 1.0):
        c.circle(cx, cy, maxr * lvl, stroke=1, fill=0)

    # Axis spokes
    for i in range(6):
        a = math.radians(90 - 60 * i)
        c.setStrokeColor(TAUPE)
        c.setLineWidth(1.0)
        c.line(cx, cy, cx + maxr * math.cos(a), cy + maxr * math.sin(a))

    # Polygons: draw the larger area first (Engineered), then Naive on top
    eng = polygon_points(cx, cy, maxr, ENGINEERED)
    nai = polygon_points(cx, cy, maxr, NAIVE)
    fill_polygon(c, eng, EMERALD, 0.40)
    stroke_polygon(c, eng, EMERALD, 3.2)
    fill_polygon(c, nai, BURGUNDY, 0.45)
    stroke_polygon(c, nai, BURGUNDY, 3.2)

    # Vertex dots (full alpha, on top)
    for (px, py) in eng:
        c.setFillColor(EMERALD)
        c.circle(px, py, 5, stroke=0, fill=1)
    for (px, py) in nai:
        c.setFillColor(BURGUNDY)
        c.circle(px, py, 5, stroke=0, fill=1)

    # Axis labels (quadrant-aware alignment)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16.5)
    for i, label in enumerate(AXES):
        a = math.radians(90 - 60 * i)
        ca, sa = math.cos(a), math.sin(a)
        lr = maxr + 26
        lx = cx + lr * ca
        ly = cy + lr * sa - 6
        if sa > 0.5:
            ly += 16
        elif sa < -0.5:
            ly -= 16
        if ca > 0.3:
            c.drawString(lx, ly, label)
        elif ca < -0.3:
            c.drawRightString(lx, ly, label)
        else:
            c.drawCentredString(lx, ly, label)

    # Legend (bottom, centered, two items)
    items = [(BURGUNDY, 'Naive prompt'), (EMERALD, 'Engineered prompt')]
    c.setFont('Poppins-Medium', 17)
    gap = 360
    total = gap
    start_x = W / 2 - total / 2
    ly = 96
    for k, (col, lab) in enumerate(items):
        ix = start_x + k * gap
        c.setFillColor(col)
        c.circle(ix, ly + 5, 12, stroke=0, fill=1)
        c.setFillColor(GRAPHITE)
        c.drawString(ix + 22, ly, lab)


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    tmp_png = '/tmp/_diagram3_hi'
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile', OUTPUT_PDF, tmp_png],
                   check=True)
    img = Image.open(tmp_png + '.png').convert('RGB')
    img = img.resize((W, H), Image.LANCZOS)
    img.save(OUTPUT_PNG)
    print('Rendered: ' + OUTPUT_PNG + '  size=' + str(img.size))


if __name__ == '__main__':
    main()
