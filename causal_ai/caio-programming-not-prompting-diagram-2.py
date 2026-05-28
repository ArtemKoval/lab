#!/usr/bin/env python3
"""
CAIO Diagram: Prompt Craft vs. Programmed Systems
Topic: programming-not-prompting
Type: Radar / spider overlay — multi-dimensional comparison of two approaches
Output: caio-programming-not-prompting-diagram-2.png
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
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-programming-not-prompting-diagram-2.png'
OUTPUT_PDF = '/tmp/_d2.pdf'

AXES = ["Portability", "Maintainability", "Measurability",
        "Model\nindependence", "Optimizability", "Reusability"]
MAXV = 5

# scores 0..5
PROMPT_CRAFT = [1, 2, 1, 1, 1, 2]
PROGRAMMED   = [5, 5, 5, 5, 5, 4]


def polygon_points(cx, cy, r_max, values, n):
    pts = []
    for i, v in enumerate(values):
        ang = math.radians(90 - i * (360 / n))
        r = r_max * (v / MAXV)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def draw_polygon(c, pts, fill_color, alpha):
    p = c.beginPath()
    p.moveTo(*pts[0])
    for x, y in pts[1:]:
        p.lineTo(x, y)
    p.close()
    c.setFillColor(fill_color)
    c.setStrokeColor(fill_color)
    c.setLineWidth(3)
    c.setFillAlpha(alpha)
    c.setStrokeAlpha(1.0)
    c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1.0)
    # vertex dots
    for x, y in pts:
        c.setFillColor(fill_color)
        c.circle(x, y, 6, stroke=0, fill=1)


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 70, "Prompt Craft vs. Programmed Systems")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 100, "The same comparison every AI portfolio faces, across the dimensions that decide durability")

    cx, cy = W / 2, 545
    r_max = 330
    n = len(AXES)

    # gridlines (concentric polygons)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(1.2)
    for level in [0.2, 0.4, 0.6, 0.8, 1.0]:
        pts = []
        for i in range(n):
            ang = math.radians(90 - i * (360 / n))
            r = r_max * level
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        p = c.beginPath()
        p.moveTo(*pts[0])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    # spokes
    for i in range(n):
        ang = math.radians(90 - i * (360 / n))
        c.setStrokeColor(TAUPE)
        c.setLineWidth(1.2)
        c.line(cx, cy, cx + r_max * math.cos(ang), cy + r_max * math.sin(ang))

    # polygons — draw larger (programmed) first, smaller (prompt craft) on top
    draw_polygon(c, polygon_points(cx, cy, r_max, PROGRAMMED, n), EMERALD, 0.32)
    draw_polygon(c, polygon_points(cx, cy, r_max, PROMPT_CRAFT, n), BURGUNDY, 0.40)

    # axis labels at tips, quadrant-aware
    c.setFont('Poppins-Medium', 17)
    for i, label in enumerate(AXES):
        ang = math.radians(90 - i * (360 / n))
        lx = cx + (r_max + 36) * math.cos(ang)
        ly = cy + (r_max + 36) * math.sin(ang)
        cos_v = math.cos(ang)
        lines = label.split("\n")
        c.setFillColor(NAVY)
        # vertical block centering
        leading = 20
        first_y = ly + (len(lines) - 1) * leading / 2
        for j, ln in enumerate(lines):
            yy = first_y - j * leading
            if cos_v > 0.3:
                c.drawString(lx, yy, ln)
            elif cos_v < -0.3:
                c.drawRightString(lx, yy, ln)
            else:
                c.drawCentredString(lx, yy, ln)

    # legend (bottom)
    ly = 64
    # swatch 1
    c.setFillColor(BURGUNDY)
    c.setFillAlpha(0.40)
    c.rect(W / 2 - 360, ly, 28, 28, stroke=0, fill=1)
    c.setFillAlpha(1.0)
    c.setStrokeColor(BURGUNDY)
    c.setLineWidth(2)
    c.rect(W / 2 - 360, ly, 28, 28, stroke=1, fill=0)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 18)
    c.drawString(W / 2 - 322, ly + 7, "Prompt craft — the artisanal model")
    # swatch 2
    c.setFillColor(EMERALD)
    c.setFillAlpha(0.32)
    c.rect(W / 2 + 40, ly, 28, 28, stroke=0, fill=1)
    c.setFillAlpha(1.0)
    c.setStrokeColor(EMERALD)
    c.setLineWidth(2)
    c.rect(W / 2 + 40, ly, 28, 28, stroke=1, fill=0)
    c.setFillColor(NAVY)
    c.drawString(W / 2 + 78, ly + 7, "Programmed systems")


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
