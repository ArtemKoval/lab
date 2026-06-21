#!/usr/bin/env python3
"""
CAIO Diagram: Delivered Capability Is an Intersection
Topic: delivered-capability
Type: Three-circle Venn (model peak / governance / context; center = delivered)
Output: caio-delivered-capability-diagram-3.png
"""

import os
import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

# --- Palette (CAIO standard) ---
NAVY = HexColor('#1E2A4A')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
MUSTARD = HexColor('#C4952A')
WHITE = HexColor('#FFFFFF')

# Translucent lobe fills (alpha blend over white)
PEAK_A = Color(0.102, 0.227, 0.420, 0.50)   # sapphire, rented
GOV_A = Color(0.102, 0.361, 0.227, 0.50)    # emerald, owned
CTX_A = Color(0.353, 0.176, 0.416, 0.50)    # amethyst, owned

# Opaque ring strokes
PEAK_S = HexColor('#1A3A6B')
GOV_S = HexColor('#1A5C3A')
CTX_S = HexColor('#5A2D6A')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PNG = os.path.join(BASE, 'caio-delivered-capability-diagram-3.png')
OUTPUT_PDF = os.path.join(BASE, '_diagram3_temp.pdf')


def tag(c, x, y, text, fill, text_color):
    """Small rounded pill tag."""
    c.setFont('Poppins-Bold', 13)
    w = c.stringWidth(text, 'Poppins-Bold', 13)
    pad = 11
    c.setFillColor(fill)
    c.roundRect(x - w / 2 - pad, y - 10, w + 2 * pad, 26, 11, stroke=0, fill=1)
    c.setFillColor(text_color)
    c.drawCentredString(x, y - 2, text)


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title and subtitle
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, 1128, 'Delivered Capability Is an Intersection')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, 1090, 'What users receive is where a rented model meets governance and context you own')

    cx, cy = 800, 560
    R = 232
    d = 138

    # Circle centers
    ax, ay = cx, cy + d                                  # top: Model Peak
    bx, by = cx - d * math.cos(math.radians(30)), cy - d * math.sin(math.radians(30))  # lower-left: Governance
    ccx, ccy = cx + d * math.cos(math.radians(30)), cy - d * math.sin(math.radians(30))  # lower-right: Context

    # Filled translucent lobes
    for (px, py), fill in [((ax, ay), PEAK_A), ((bx, by), GOV_A), ((ccx, ccy), CTX_A)]:
        c.setFillColor(fill)
        c.circle(px, py, R, stroke=0, fill=1)
    # reset alpha
    c.setFillColor(NAVY)

    # Opaque ring outlines
    c.setLineWidth(3)
    for (px, py), stroke in [((ax, ay), PEAK_S), ((bx, by), GOV_S), ((ccx, ccy), CTX_S)]:
        c.setStrokeColor(stroke)
        c.circle(px, py, R, stroke=1, fill=0)

    # Lobe labels (in the non-overlapping outer region of each circle)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(ax, ay + 118, 'Model peak')
    c.setFont('Poppins', 15)
    c.drawCentredString(ax, ay + 92, 'raw capability, on a fixed test')
    tag(c, ax, ay + 150, 'RENTED', PEAK_S, IVORY)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(bx - 28, by - 96, 'Governance')
    c.setFont('Poppins', 15)
    c.drawCentredString(bx - 28, by - 120, 'routing, gates, refusals')
    tag(c, bx - 28, by - 146, 'OWNED', GOV_S, IVORY)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(ccx + 28, ccy - 96, 'Context')
    c.setFont('Poppins', 15)
    c.drawCentredString(ccx + 28, ccy - 120, 'your data, retrieval, evals')
    tag(c, ccx + 28, ccy - 146, 'OWNED', CTX_S, IVORY)

    # Center badge: the triple intersection = delivered
    bcx, bcy = cx, cy
    c.setFillColor(NAVY)
    c.setStrokeColor(OCHRE)
    c.setLineWidth(4)
    c.circle(bcx, bcy, 82, stroke=1, fill=1)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(bcx, bcy + 14, 'DELIVERED')
    c.setFont('Poppins', 13)
    c.drawCentredString(bcx, bcy - 8, 'what users')
    c.drawCentredString(bcx, bcy - 26, 'receive')

    # Bottom takeaway
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 18)
    c.drawCentredString(W / 2, 56, 'Delivered capability lives where all three overlap. Two of the three are yours.')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                    OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    if os.path.exists(OUTPUT_PDF):
        os.remove(OUTPUT_PDF)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
