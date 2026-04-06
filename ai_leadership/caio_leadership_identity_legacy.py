#!/usr/bin/env python3
"""
CAIO Diagram: AI-Enabled vs AI-Ready — Leadership Maturity Radar
Topic: leadership-identity-legacy
Type: Radar / spider overlay
Output: caio-leadership-identity-legacy-diagram-2.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')

# --- Fonts ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-leadership-identity-legacy-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'

DIMENSIONS = [
    "Strategic\nVision",
    "Technical\nDepth",
    "Cultural\nInfluence",
    "Ethical\nGovernance",
    "Talent\nRetention",
    "Ecosystem\nVoice",
    "Foresight\nCapacity",
]
ENABLED = [8, 7, 4, 5, 4, 3, 3]
READY = [9, 8, 8, 9, 8, 7, 8]
MAX_VAL = 10


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 70, "AI-Enabled vs. AI-Ready")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 105, "The maturity gap that separates deployment from lasting organizational transformation")

    cx, cy = W / 2, 520
    max_r = 320
    n = len(DIMENSIONS)

    def angle_for(i):
        return math.radians(90 - i * (360 / n))

    # Grid rings at 25%, 50%, 75%, 100%
    for frac in [0.25, 0.5, 0.75, 1.0]:
        r = max_r * frac
        c.setStrokeColor(HexColor('#D0D0D0'))
        c.setLineWidth(0.7)
        pts = []
        for i in range(n):
            a = angle_for(i)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for pt in pts[1:]:
            p.lineTo(pt[0], pt[1])
        p.close()
        c.drawPath(p, stroke=1, fill=0)

        # Scale label at 12 o'clock spoke
        if frac in [0.5, 1.0]:
            c.setFillColor(HexColor('#999999'))
            c.setFont('Poppins', 11)
            c.drawString(cx + 5, cy + r + 3, str(int(MAX_VAL * frac)))

    # Spokes
    for i in range(n):
        a = angle_for(i)
        c.setStrokeColor(HexColor('#D0D0D0'))
        c.setLineWidth(0.7)
        c.line(cx, cy, cx + max_r * math.cos(a), cy + max_r * math.sin(a))

    # Dimension labels
    for i, dim in enumerate(DIMENSIONS):
        a = angle_for(i)
        label_r = max_r + 55
        lx = cx + label_r * math.cos(a)
        ly = cy + label_r * math.sin(a)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 14)
        lines = dim.split('\n')
        for li, line in enumerate(lines):
            c.drawCentredString(lx, ly - li * 18, line)

    # Draw polygon
    def draw_poly(data, fill_color, stroke_color, alpha=0.25):
        pts = []
        for i, v in enumerate(data):
            a = angle_for(i)
            r = max_r * (v / MAX_VAL)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for pt in pts[1:]:
            p.lineTo(pt[0], pt[1])
        p.close()
        c.saveState()
        c.setFillAlpha(alpha)
        c.setFillColor(fill_color)
        c.setStrokeColor(stroke_color)
        c.setLineWidth(2.5)
        c.drawPath(p, stroke=1, fill=1)
        c.restoreState()
        # Data point dots
        for pt in pts:
            c.setFillColor(stroke_color)
            c.circle(pt[0], pt[1], 5, stroke=0, fill=1)

    # Draw AI-Ready first (behind), then AI-Enabled on top
    draw_poly(READY, EMERALD, EMERALD, 0.2)
    draw_poly(ENABLED, OCHRE, OCHRE, 0.35)

    # Legend
    legend_y = 85
    # AI-Enabled
    c.setFillColor(OCHRE)
    c.circle(560, legend_y + 5, 10, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 15)
    c.drawString(580, legend_y - 2, "AI-Enabled Organization (avg 4.9/10)")

    # AI-Ready
    c.setFillColor(EMERALD)
    c.circle(560, legend_y - 30 + 5, 10, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.drawString(580, legend_y - 32, "AI-Ready Organization (avg 8.1/10)")


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
