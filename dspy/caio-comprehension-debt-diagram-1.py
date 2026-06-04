#!/usr/bin/env python3
"""
CAIO Diagram: Adoption Outran Trust
Topic: comprehension-debt
Type: Pictogram ring (data-driven circular arrangement, filled vs. empty)
Output: caio-comprehension-debt-diagram-1.png
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

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-comprehension-debt-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1.pdf'


def vcentre(c, x, y, text, font, size, color):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawCentredString(x, y - size * 0.35, text)


def draw_diagram(c):
    # Background
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title + subtitle
    vcentre(c, W / 2, 1128, "Adoption Outran Trust", 'Poppins-Bold', 34, NAVY)
    vcentre(c, W / 2, 1082, "84% of developers use AI tools. 33% trust what it produces.",
            'Poppins-Light', 18, GRAPHITE)

    # Pictogram ring of 12 circles
    cx, cy = 800, 560
    orbit = 300
    r = 47
    total = 12
    filled = 4  # 4/12 = 33%
    for i in range(total):
        ang = math.radians(90 - i * (360 / total))  # clockwise from top
        x = cx + orbit * math.cos(ang)
        y = cy + orbit * math.sin(ang)
        if i < filled:
            c.setFillColor(EMERALD)
            c.circle(x, y, r, stroke=0, fill=1)
        else:
            c.setStrokeColor(TAUPE)
            c.setLineWidth(3.5)
            c.setFillColor(WHITE)
            c.circle(x, y, r, stroke=1, fill=1)

    # Central KPI
    vcentre(c, cx, cy + 14, "33%", 'Poppins-Bold', 70, NAVY)
    vcentre(c, cx, cy - 44, "trust AI output", 'Poppins-Medium', 22, NAVY)

    # Legend
    ly = 158
    # swatch 1 (filled emerald)
    c.setFillColor(EMERALD)
    c.circle(520, ly, 16, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins', 17)
    c.drawString(548, ly - 6, "Trust accuracy of AI output  (33%)")
    # swatch 2 (empty)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(3.5)
    c.setFillColor(WHITE)
    c.circle(520, ly - 46, 16, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins', 17)
    c.drawString(548, ly - 52, "Distrust or remain neutral  (67%)")

    # Source line
    vcentre(c, W / 2, 74, "Stack Overflow Developer Survey, 2025", 'Poppins-Light', 15, GRAPHITE)


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
