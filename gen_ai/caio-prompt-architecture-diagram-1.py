#!/usr/bin/env python3
"""
CAIO Diagram: The Four Dimensions of a Production Prompt
Topic: prompt-architecture
Type: Segmented wheel
Output: caio-prompt-architecture-diagram-1.png
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

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-prompt-architecture-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title + subtitle
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, 1132, 'The Four Dimensions of a Production Prompt')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, 1092, 'A structured instruction removes the guesswork a model would otherwise fill in')

    cx, cy = W / 2, 510
    outer_r = 350
    hub_r = 118

    sectors = [
        # (start_angle, label, descriptor, fill)
        (45,  'ROLE',        'who the system acts as',   SAPPHIRE),
        (135, 'ACTION',      'what it must do',          EMERALD),
        (225, 'CONTEXT',     'situation and constraints', BURGUNDY),
        (315, 'EXPECTATION', 'the shape of the answer',  AMETHYST),
    ]

    # Draw filled wedges with white separators
    for start, label, desc, fill in sectors:
        c.setFillColor(fill)
        c.setStrokeColor(WHITE)
        c.setLineWidth(4)
        c.wedge(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r, start, 90, stroke=1, fill=1)

    # Sector labels at mid-angle
    label_r = 232
    for start, label, desc, fill in sectors:
        mid = math.radians(start + 45)
        lx = cx + label_r * math.cos(mid)
        ly = cy + label_r * math.sin(mid)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 31)
        c.drawCentredString(lx, ly + 6, label)
        c.setFont('Poppins', 16)
        c.drawCentredString(lx, ly - 24, desc)

    # Central hub (white fill, navy ring)
    c.setFillColor(WHITE)
    c.setStrokeColor(NAVY)
    c.setLineWidth(4)
    c.circle(cx, cy, hub_r, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 26)
    c.drawCentredString(cx, cy + 8, 'Structured')
    c.drawCentredString(cx, cy - 24, 'Prompt')

    # Caption beneath wheel
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(cx, 118, 'Each constraint removes a degree of freedom — turning a probabilistic gamble into a repeatable result')


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    import subprocess
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile', OUTPUT_PDF,
                    OUTPUT_PNG.replace('.png', '')], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
