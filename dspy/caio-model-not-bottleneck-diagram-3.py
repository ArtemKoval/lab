#!/usr/bin/env python3
"""
CAIO Diagram: The Adoption-to-Advantage Gap
Topic: model-not-bottleneck
Type: Progress rings (concentric percentage arcs, Apple Watch style)
Output: caio-model-not-bottleneck-diagram-3.png
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
TAUPE = HexColor('#8A7B6B')
UMBER = HexColor('#6B4226')
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-model-not-bottleneck-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'

CX, CY = 540, 540


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 36)
    c.drawCentredString(800, 1132, 'The Adoption-to-Advantage Gap')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 17)
    c.drawCentredString(800, 1092, 'Share of organizations, by depth of AI deployment   |   Art Koval')

    # rings: (pct, color, legend_label) outer to inner
    rings = [
        (88, EMERALD,  'Use AI in at least one function'),
        (31, SAPPHIRE, 'Scaling AI enterprise-wide'),
        (23, AMETHYST, 'Scaling agents in 1+ function'),
        (9,  BURGUNDY, 'Scaled agents to tangible value (<10%)'),
    ]
    radii = [330, 255, 180, 105]
    ring_w = 34

    c.setLineCap(1)  # round caps
    for (pct, color, _), r in zip(rings, radii):
        # background ring
        c.setStrokeColor(TAUPE)
        c.setLineWidth(ring_w)
        c.circle(CX, CY, r, stroke=1, fill=0)
        # progress arc from 12 o'clock, clockwise
        extent = -(pct / 100.0) * 360.0
        c.setStrokeColor(color)
        c.setLineWidth(ring_w)
        p = c.beginPath()
        p.arc(CX - r, CY - r, CX + r, CY + r, 90, extent)
        c.drawPath(p, stroke=1, fill=0)
    c.setLineCap(0)

    # Legend on the right
    lx_dot = 985
    lx_pct = 1015
    lx_lab = 1110
    rows_y = [690, 605, 520, 435]
    for (pct, color, label), y in zip(rings, rows_y):
        c.setFillColor(color)
        c.circle(lx_dot, y + 6, 13, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 30)
        disp = '<10%' if pct == 9 else f'{pct}%'
        c.drawString(lx_pct, y, disp)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 16)
        c.drawString(lx_lab, y + 16, label.split(' (')[0] if '(' in label else label)
        if pct == 9:
            c.setFont('Poppins', 14)
            c.drawString(lx_lab, y - 6, 'fewer than one in ten')

    # caption under legend
    c.setFillColor(EMERALD)
    c.setFont('Poppins-Medium', 16)
    c.drawString(lx_pct, 360, 'Access is common. Advantage is rare.')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    import subprocess
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                    OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
