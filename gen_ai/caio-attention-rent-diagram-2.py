#!/usr/bin/env python3
"""
CAIO Diagram: Four Layers That Compound
Topic: attention-rent
Type: Segmented wheel (donut, four equal sectors) — the owned layers built atop a rented model
Output: caio-attention-rent-diagram-2.png
"""

import math
import subprocess
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

pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-attention-rent-diagram-2.png'
OUTPUT_PDF = '/tmp/_d2.pdf'

CX, CY = 800, 545
RO = 348                 # outer radius
RI = 142                 # inner radius (donut hole)
RH = 134                 # hub circle radius
MIDR = 246               # label band centerline

# sector: (start_angle_ccw_from_3oclock, fill, [title lines], gloss)
SECTORS = [
    (45,  EMERALD,  ["Evaluation"],            "measure how it behaves"),
    (135, SAPPHIRE, ["Governed", "Context"],   "control what it sees"),
    (225, BURGUNDY, ["Constraints"],           "bound what it may do"),
    (315, AMETHYST, ["Observability"],         "watch it in production"),
]
EXTENT = 90
BOUNDARIES = (45, 135, 225, 315)


def pos(angle_deg, radius):
    a = math.radians(angle_deg)
    return CX + radius * math.cos(a), CY + radius * math.sin(a)


def draw_label_block(c, lx, ly, title_lines, gloss):
    title_fs, gloss_fs = 22, 13
    title_lh, gloss_lh = 30, 20
    total = len(title_lines) * title_lh + gloss_lh
    top = ly + total / 2
    cursor = top - title_lh + 7
    c.setFillColor(IVORY)
    for line in title_lines:
        c.setFont('Poppins-Bold', title_fs)
        c.drawCentredString(lx, cursor, line)
        cursor -= title_lh
    c.setFont('Poppins-Light', gloss_fs)
    c.drawCentredString(lx, cursor - 2, gloss)


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title and subtitle
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 31)
    c.drawCentredString(CX, H - 80, "Four Layers That Compound")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 17)
    c.drawCentredString(CX, H - 114, "Rent the model underneath. Own the layers that turn it into an advantage.")

    # Colored sectors
    bx0, by0, bx1, by1 = CX - RO, CY - RO, CX + RO, CY + RO
    for start, fill, _, _ in SECTORS:
        c.setFillColor(fill)
        c.setStrokeColor(fill)
        c.setLineWidth(1)
        c.wedge(bx0, by0, bx1, by1, start, EXTENT, stroke=1, fill=1)

    # White separators at the true sector boundaries
    c.setStrokeColor(WHITE)
    c.setLineWidth(9)
    for b in BOUNDARIES:
        ix, iy = pos(b, RI - 2)
        ox, oy = pos(b, RO + 2)
        c.line(ix, iy, ox, oy)

    # Donut hole + Ivory hub
    c.setFillColor(WHITE)
    c.circle(CX, CY, RI, stroke=0, fill=1)
    c.setFillColor(IVORY)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2.5)
    c.circle(CX, CY, RH, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 25)
    c.drawCentredString(CX, CY + 12, "OWNED")
    c.drawCentredString(CX, CY - 20, "ADVANTAGE")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(CX, CY - 50, "what compounds")

    # Sector labels
    for start, _, title_lines, gloss in SECTORS:
        center_ang = start + EXTENT / 2
        lx, ly = pos(center_ang, MIDR)
        draw_label_block(c, lx, ly, title_lines, gloss)

    # Bottom caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 17)
    c.drawCentredString(CX, 112, "The model is interchangeable. These four are not.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(CX, 82, "They hold their value as models churn beneath them.")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                    OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    # normalize supersampled raster to exact 1600x1200 deliverable dimensions
    from PIL import Image
    Image.open(OUTPUT_PNG).resize((W, H), Image.LANCZOS).save(OUTPUT_PNG)
    print("Rendered:", OUTPUT_PNG)


if __name__ == '__main__':
    main()
