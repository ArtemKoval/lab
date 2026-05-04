#!/usr/bin/env python3
"""
CAIO Diagram: Anatomy of a Structural Causal Model
Topic: structural-causal-models
Type: Mindmap / Hub-and-Spoke
Output: caio-structural-causal-models-diagram-1.png
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

# --- Fonts ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-structural-causal-models-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W/2, H - 70, "Anatomy of a Structural Causal Model")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 105, "Four components that turn a graph of relationships into a model of mechanism")

    # Center hub
    cx, cy = W/2, 540
    hub_r = 110
    orbit_r = 360
    spoke_r = 130

    # Spokes — 4 satellites at 45°, 135°, 225°, 315° from center
    spokes = [
        # (angle_deg, fill, label_top, label_bottom, description)
        (135, SAPPHIRE,    "Endogenous",        "Variables",
         "The variables\nyou model explicitly"),
        (45,  EMERALD,     "Exogenous",         "Variables",
         "Latent stand-ins\nfor unmodeled causes"),
        (315, BURGUNDY,    "Assignment",        "Functions",
         "How each effect is\nset by its causes"),
        (225, AMETHYST,    "Exogenous",         "Distributions",
         "Probability of the\nunmodeled variation"),
    ]

    # Draw connector lines first (behind nodes)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(2.5)
    for angle_deg, *_ in spokes:
        ang = math.radians(angle_deg)
        sx = cx + (hub_r + 5) * math.cos(ang)
        sy = cy + (hub_r + 5) * math.sin(ang)
        ex = cx + (orbit_r - spoke_r - 5) * math.cos(ang)
        ey = cy + (orbit_r - spoke_r - 5) * math.sin(ang)
        c.line(sx, sy, ex, ey)

    # Draw central hub
    c.setFillColor(NAVY)
    c.circle(cx, cy, hub_r, stroke=0, fill=1)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 26)
    c.drawCentredString(cx, cy + 12, "SCM")
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(cx, cy - 12, "Structural")
    c.drawCentredString(cx, cy - 30, "Causal Model")

    # Draw spokes
    for angle_deg, fill, label_top, label_bottom, description in spokes:
        ang = math.radians(angle_deg)
        sx = cx + orbit_r * math.cos(ang)
        sy = cy + orbit_r * math.sin(ang)

        # Spoke circle
        c.setFillColor(fill)
        c.circle(sx, sy, spoke_r, stroke=0, fill=1)

        # Two-line label inside spoke (Ivory text on dark fill — AAA)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 19)
        c.drawCentredString(sx, sy + 12, label_top)
        c.drawCentredString(sx, sy - 14, label_bottom)

        # Description below spoke (Navy on white — AAA)
        c.setFillColor(NAVY)
        c.setFont('Poppins', 13)
        desc_y = sy - spoke_r - 28
        for line in description.split('\n'):
            c.drawCentredString(sx, desc_y, line)
            desc_y -= 18

    # Bottom caption
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 14)
    c.drawCentredString(
        W/2, 80, "Together, these components encode not just what causes what — but how causes affect effects")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()

    import subprocess
    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
