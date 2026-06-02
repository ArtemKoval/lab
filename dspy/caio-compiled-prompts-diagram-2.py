#!/usr/bin/env python3
"""
CAIO Diagram: Four Families of Prompt Optimizers
Topic: compiled-prompts (AWS, reversible model choice)
Type: Segmented wheel
Output: caio-compiled-prompts-diagram-2.png
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
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TAUPE = HexColor('#8A7B6B')

pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-compiled-prompts-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'

CX, CY = 800, 540
R = 380
HUB_R = 122

# (title1, title2, descriptor, fill, start_ang) ; clockwise sectors of 90 deg
SECTORS = [
    ("Labeled", "Few-Shot", "random demos", SAPPHIRE, 90),
    ("Bootstrap", "Few-Shot", "rejection-sampled", EMERALD, 0),
    ("Bootstrap +", "Search", "best of many sets", BURGUNDY, -90),
    ("Nearest", "Neighbor", "per-request demos", AMETHYST, -180),
]


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(CX, 1138, "Four Families of Prompt Optimizers")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(CX, 1100, "Each adapts demonstrations to your data \u2014 choice follows the task's shape")

    # Sectors (clockwise, negative extent), white separators
    for t1, t2, desc, fill, start in SECTORS:
        c.setFillColor(fill)
        c.setStrokeColor(HexColor('#FFFFFF'))
        c.setLineWidth(3)
        c.wedge(CX - R, CY - R, CX + R, CY + R, start, -90, stroke=1, fill=1)

    # Labels at sector mid-angles
    for t1, t2, desc, fill, start in SECTORS:
        mid = math.radians(start - 45)
        lx = CX + (R * 0.60) * math.cos(mid)
        ly = CY + (R * 0.60) * math.sin(mid)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 21)
        c.drawCentredString(lx, ly + 20, t1)
        c.drawCentredString(lx, ly - 6, t2)
        c.setFont('Poppins', 15)
        c.drawCentredString(lx, ly - 32, desc)

    # Hub
    c.setFillColor(HexColor('#FFFFFF'))
    c.circle(CX, CY, HUB_R, stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.circle(CX, CY, HUB_R, stroke=1, fill=0)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 20)
    c.drawCentredString(CX, CY + 10, "Demonstration")
    c.setFont('Poppins-Medium', 18)
    c.drawCentredString(CX, CY - 18, "Optimization")


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
