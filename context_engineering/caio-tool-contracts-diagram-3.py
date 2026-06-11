#!/usr/bin/env python3
"""
CAIO Diagram: Discipline Gap in the Agent Era
Topic: caio-tool-contracts
Type: Progress rings (concentric completion arcs)
Output: caio-tool-contracts-diagram-3.png
"""

import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
TAUPE_SOFT = HexColor('#D9D2C6')

FONT_DIR = '/usr/share/fonts/truetype/google-fonts/'
pdfmetrics.registerFont(TTFont('Poppins', FONT_DIR + 'Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', FONT_DIR + 'Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', FONT_DIR + 'Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', FONT_DIR + 'Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Italic', FONT_DIR + 'Poppins-Italic.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-tool-contracts-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'

CX, CY = 520, 520
RING_W = 44

METRICS = [
    (42, BURGUNDY, 330, '42%', 'abandoned most AI initiatives in 2025, double the prior year',
     'S&P Global Market Intelligence, 2025'),
    (25, EMERALD, 248, '25%', 'of AI initiatives delivered the ROI leadership expected',
     'IBM Institute for Business Value, 2025'),
    (2, SAPPHIRE, 166, '2%', 'of organizations have integrated more than half of their apps',
     'MuleSoft Connectivity Benchmark, 2025'),
]


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 31)
    c.drawCentredString(W / 2, 1132, 'Discipline Gap in the Agent Era')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(W / 2, 1098,
                        'Three verified numbers behind stalled AI programs  —  Chief AI Officer Insights')

    c.setLineCap(1)

    for value, col, r, big, line1, org in METRICS:
        # Background ring
        c.setStrokeColor(TAUPE_SOFT)
        c.setLineWidth(RING_W)
        c.circle(CX, CY, r, stroke=1, fill=0)
        # Completion arc, clockwise from 12 o'clock (negative extent)
        extent = (value / 100.0) * 360.0
        c.setStrokeColor(col)
        c.setLineWidth(RING_W)
        p = c.beginPath()
        p.arc(CX - r, CY - r, CX + r, CY + r, 90, -extent)
        c.drawPath(p, stroke=1, fill=0)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 40)
    c.drawCentredString(CX, CY - 14, '2025')

    # Right-hand legend
    lx = 1010
    ly = 790
    for value, col, r, big, line1, org in METRICS:
        c.setFillColor(col)
        c.circle(lx + 14, ly + 8, 13, stroke=0, fill=1)
        c.setFillColor(col)
        c.setFont('Poppins-Bold', 34)
        c.drawString(lx + 44, ly - 4, big)
        c.setFillColor(NAVY)
        c.setFont('Poppins', 15)
        c.drawString(lx + 44, ly - 32, line1)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 13)
        c.drawString(lx + 44, ly - 56, org)
        ly -= 135

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Italic', 13.5)
    c.drawString(lx + 44, ly + 28, 'Capability was rented successfully.')
    c.drawString(lx + 44, ly + 6, 'Connection was never engineered.')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run([
        'pdftoppm', '-png', '-r', '150', '-singlefile',
        OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print('Rendered: ' + OUTPUT_PNG)


if __name__ == '__main__':
    main()
