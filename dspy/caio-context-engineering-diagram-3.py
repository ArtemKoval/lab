#!/usr/bin/env python3
"""
CAIO Diagram: Evolution of LLM-Based Systems
Topic: context-engineering
Type: Archimedean spiral (4 growing nodes)
Output: caio-context-engineering-diagram-3.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

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
UMBER = HexColor('#6B4226')
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-context-engineering-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'

CX, CY = 790, 520
B = 51.4  # spiral growth: r = B * theta (theta in radians)


def centred(c, x, y, text, font, size, color):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawCentredString(x, y - size * 0.35, text)


def spiral_xy(theta):
    r = B * theta
    return CX + r * math.cos(theta), CY + r * math.sin(theta)


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    centred(c, W / 2, 1134, "Evolution of LLM-Based Systems", 'Poppins-Bold', 33, NAVY)
    centred(c, W / 2, 1088, "Each stage outward adds capability, and more context to manage", 'Poppins-Light', 18, GRAPHITE)

    # Spiral path
    c.setStrokeColor(TAUPE)
    c.setLineWidth(3)
    p = c.beginPath()
    theta = 0.35
    x0, y0 = spiral_xy(theta)
    p.moveTo(x0, y0)
    while theta <= 8.45:
        theta += 0.05
        x, y = spiral_xy(theta)
        p.lineTo(x, y)
    c.drawPath(p, stroke=1, fill=0)

    # nodes: (theta, node_radius, fill, number, (label, descriptor), (label_x, label_y))
    nodes = [
        (1.571, 36, SAPPHIRE,  "1", ("Single LLM call", "stateless prompt to reply"), (790, 690)),
        (3.84,  48, TEAL,      "2", ("AI workflow",      "chained steps + RAG"),       (545, 318)),
        (6.11,  60, AMETHYST,  "3", ("AI agent",         "reasons, plans, acts"),      (1255, 455)),
        (8.38,  76, BURGUNDY,  "4", ("Agentic system",   "coordinated agents"),        (405, 912)),
    ]

    for theta, nr, fill, num, (l1, l2), (lx, ly) in nodes:
        x, y = spiral_xy(theta)
        c.setFillColor(fill)
        c.setStrokeColor(WHITE)
        c.setLineWidth(4)
        c.circle(x, y, nr, stroke=1, fill=1)
        centred(c, x, y, num, 'Poppins-Bold', int(nr * 0.85), IVORY)
        centred(c, lx, ly + 12, l1, 'Poppins-Bold', 20, NAVY)
        centred(c, lx, ly - 13, l2, 'Poppins-Light', 14, GRAPHITE)


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    import subprocess
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                    OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    print("Rendered:", OUTPUT_PNG)


if __name__ == '__main__':
    main()
