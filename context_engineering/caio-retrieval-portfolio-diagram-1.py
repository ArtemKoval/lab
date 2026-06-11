#!/usr/bin/env python3
"""
CAIO standalone diagram 1: Seven grounding architectures
Pattern: segmented wheel with outer descriptors
Canvas: 1600x1200, white background, no footer
Output: caio-retrieval-portfolio-diagram-1.pdf
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
TAUPE = HexColor('#8A7B6B')
UMBER = HexColor('#6B4226')
WHITE = HexColor('#FFFFFF')

FP = '/usr/share/fonts/truetype/google-fonts/'
pdfmetrics.registerFont(TTFont('Poppins', FP + 'Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', FP + 'Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', FP + 'Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', FP + 'Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Italic', FP + 'Poppins-Italic.ttf'))

W, H = 1600, 1200
OUT = '/home/claude/caio-retrieval-portfolio-diagram-1.pdf'


def pt(cx, cy, r, deg):
    """Point on a circle at angle deg, counterclockwise from east."""
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def main():
    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title block
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 52)
    c.drawCentredString(W / 2, 1108, 'Seven grounding architectures')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 24)
    c.drawCentredString(W / 2, 1062,
                        'One portfolio decision, seven interchangeable retrieval patterns')

    cx, cy, R, hub = 800, 520, 340, 128
    names = ['RAG', 'GRAPH', 'HYBRID', 'AGENTIC', 'VECTORLESS', 'CACHED', 'STUFFED']
    descs = [
        ('semantic search over', 'embedded chunks'),
        ('traversal across', 'linked entities'),
        ('lexical plus vector', 'with rank fusion'),
        ('tool-using loops', 'that plan retrieval'),
        ('reasoning over', 'document structure'),
        ('prepared context', 'reused across turns'),
        ('whole documents', 'inside the window'),
    ]
    fills = [NAVY, SAPPHIRE, EMERALD, BURGUNDY, AMETHYST, TEAL, UMBER]
    n = 7
    span = 360.0 / n

    # Wedges, clockwise from 12 o'clock (negative extent)
    for i in range(n):
        a0 = 90 - i * span
        c.setFillColor(fills[i])
        c.setStrokeColor(WHITE)
        c.setLineWidth(4)
        c.wedge(cx - R, cy - R, cx + R, cy + R, a0, -span, stroke=1, fill=1)

    # Wedge names inside, descriptors anchored outside away from the rim
    for i in range(n):
        mid = 90 - (i + 0.5) * span
        tx, ty = pt(cx, cy, 236, mid)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 21)
        c.drawCentredString(tx, ty - 7, names[i])

        line1, line2 = descs[i]
        c.setFillColor(NAVY)
        cosm = math.cos(math.radians(mid))
        if cosm > 0.35:        # right side, text grows rightward
            ox, oy = pt(cx, cy, R + 26, mid)
            c.setFont('Poppins-Medium', 19)
            c.drawString(ox, oy + 4, line1)
            c.setFont('Poppins', 18)
            c.setFillColor(GRAPHITE)
            c.drawString(ox, oy - 20, line2)
        elif cosm < -0.35:     # left side, text grows leftward
            ox, oy = pt(cx, cy, R + 26, mid)
            c.setFont('Poppins-Medium', 19)
            c.drawRightString(ox, oy + 4, line1)
            c.setFont('Poppins', 18)
            c.setFillColor(GRAPHITE)
            c.drawRightString(ox, oy - 20, line2)
        else:                  # top and bottom, centered clear of the rim
            ox, oy = pt(cx, cy, R + 44, mid)
            c.setFont('Poppins-Medium', 19)
            c.drawCentredString(ox, oy + 4, line1)
            c.setFont('Poppins', 18)
            c.setFillColor(GRAPHITE)
            c.drawCentredString(ox, oy - 20, line2)

    # Hub
    c.setFillColor(WHITE)
    c.setStrokeColor(NAVY)
    c.setLineWidth(3.5)
    c.circle(cx, cy, hub, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 10, 'GROUNDING')
    c.drawCentredString(cx, cy - 20, 'PORTFOLIO')

    # Base caption
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 20)
    c.drawCentredString(W / 2, 64,
                        'Each pattern owns a cost curve, a latency profile, and an audit surface')

    c.showPage()
    c.save()
    print('Rendered: ' + OUT)


if __name__ == '__main__':
    main()
