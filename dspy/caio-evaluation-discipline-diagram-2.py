#!/usr/bin/env python3
"""
CAIO Diagram: One Metric vs. The Whole Picture
Topic: caio-evaluation-discipline
Type: Radar / spider overlay (two layers, six axes)
Output: caio-evaluation-discipline-diagram-2.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

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
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-evaluation-discipline-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'

AXES = ["Accuracy", "Consistency", "Cost\nefficiency", "Latency",
        "Edge-case\nrobustness", "Faithfulness"]

# Normalized 0..1 scores, clockwise from top
ACCURACY_ONLY = [0.95, 0.52, 0.34, 0.42, 0.40, 0.50]
PRODUCTION    = [0.86, 0.80, 0.78, 0.74, 0.82, 0.80]


def polygon_points(cx, cy, max_r, values):
    pts = []
    n = len(values)
    for i, v in enumerate(values):
        ang = math.radians(90 - i * (360.0 / n))
        r = max_r * v
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def draw_filled_polygon(c, pts, fill_rgba, stroke_color):
    c.setFillColor(Color(fill_rgba[0], fill_rgba[1], fill_rgba[2], alpha=fill_rgba[3]))
    c.setStrokeColor(stroke_color)
    c.setLineWidth(3)
    p = c.beginPath()
    p.moveTo(pts[0][0], pts[0][1])
    for x, y in pts[1:]:
        p.lineTo(x, y)
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1.0)


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 78, "One Metric vs. The Whole Picture")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W / 2, H - 110, "When a measure becomes the target, it stops being a good measure — Goodhart's Law in one chart")

    cx, cy = W / 2, 558
    max_r = 300
    n = len(AXES)

    # Gridline polygons (Taupe, faint)
    c.setStrokeColor(TAUPE)
    for level in [0.25, 0.5, 0.75, 1.0]:
        c.setLineWidth(1 if level < 1.0 else 1.5)
        pts = polygon_points(cx, cy, max_r * level, [1.0] * n)
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    # Spokes
    c.setStrokeColor(TAUPE)
    c.setLineWidth(1)
    for i in range(n):
        ang = math.radians(90 - i * (360.0 / n))
        c.line(cx, cy, cx + max_r * math.cos(ang), cy + max_r * math.sin(ang))

    # Polygons — larger (production, balanced) first, spiky on top
    prod_pts = polygon_points(cx, cy, max_r, PRODUCTION)
    acc_pts = polygon_points(cx, cy, max_r, ACCURACY_ONLY)
    draw_filled_polygon(c, prod_pts, (0.10, 0.36, 0.23, 0.32), EMERALD)   # Emerald
    draw_filled_polygon(c, acc_pts, (0.42, 0.11, 0.16, 0.40), BURGUNDY)   # Burgundy

    # Vertex dots
    for pts, col in [(prod_pts, EMERALD), (acc_pts, BURGUNDY)]:
        c.setFillColor(col)
        for x, y in pts:
            c.circle(x, y, 4.5, stroke=0, fill=1)

    # Axis labels
    label_r = max_r + 46
    c.setFont('Poppins-Medium', 17)
    for i, label in enumerate(AXES):
        ang = math.radians(90 - i * (360.0 / n))
        lx = cx + label_r * math.cos(ang)
        ly = cy + label_r * math.sin(ang)
        cos_v = math.cos(ang)
        lines = label.split("\n")
        c.setFillColor(NAVY)
        # vertical centering for multi-line
        total_h = len(lines) * 20
        start_y = ly + (total_h / 2) - 16
        for j, ln in enumerate(lines):
            yy = start_y - j * 20
            if cos_v > 0.30:
                c.drawString(lx, yy, ln)
            elif cos_v < -0.30:
                c.drawRightString(lx, yy, ln)
            else:
                c.drawCentredString(lx, yy, ln)

    # Legend (two swatches centered near bottom)
    leg_y = 132
    items = [("Optimized for accuracy alone", BURGUNDY),
             ("Evaluated for production", EMERALD)]
    # measure widths to center the pair
    c.setFont('Poppins-Medium', 17)
    widths = [c.stringWidth(t, 'Poppins-Medium', 17) + 46 for t, _ in items]
    gap = 60
    total_w = sum(widths) + gap
    x = (W - total_w) / 2
    for (txt, col), wdt in zip(items, widths):
        c.setFillColor(col)
        c.circle(x + 11, leg_y + 6, 11, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.drawString(x + 32, leg_y, txt)
        x += wdt + gap

    # Caption
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(W / 2, 92,
                        "A system tuned to a single headline number spikes on that axis and collapses on the rest.")
    c.drawCentredString(W / 2, 68,
                        "Production readiness is the balanced shape, not the tallest point.")


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
