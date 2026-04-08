#!/usr/bin/env python3
"""
CAIO Diagram: The Inference Cost Diagnostic Framework
Topic: inference-economics
Type: Radar/Spider Overlay
Output: caio-inference-economics-diagram-1.png
"""

import math
from reportlab.lib.units import mm
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
BRICK = HexColor('#A04A2A')

# --- Font Registration ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-inference-economics-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W/2, H - 60, "The Inference Cost Diagnostic Framework")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 90, "Typical Enterprise Deployment vs Optimized Deployment")

    cx, cy = W/2, 540
    max_r = 300
    n_axes = 6
    labels = [
        "Memory\nUtilization",
        "Compute\nUtilization",
        "Latency\nPerformance",
        "Throughput\n(tokens/sec)",
        "Cost\nEfficiency",
        "Batch\nConcurrency"
    ]

    typical = [0.85, 0.25, 0.35, 0.30, 0.25, 0.20]
    optimized = [0.65, 0.80, 0.80, 0.85, 0.80, 0.75]

    # Grid rings
    for frac in [0.25, 0.5, 0.75, 1.0]:
        r = max_r * frac
        pts = []
        for i in range(n_axes):
            angle = math.radians(90 - i * (360 / n_axes))
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        p.close()
        c.setStrokeColor(HexColor('#D0D0D0'))
        c.setLineWidth(0.5)
        c.drawPath(p, stroke=1, fill=0)

        # Percentage label
        c.setFillColor(HexColor('#999999'))
        c.setFont('Poppins-Light', 10)
        c.drawString(cx + 4, cy + r + 2, f"{int(frac*100)}%")

    # Axis lines and labels
    for i in range(n_axes):
        angle = math.radians(90 - i * (360 / n_axes))
        x_end = cx + max_r * math.cos(angle)
        y_end = cy + max_r * math.sin(angle)
        c.setStrokeColor(HexColor('#CCCCCC'))
        c.setLineWidth(0.5)
        c.line(cx, cy, x_end, y_end)

        # Label
        label_r = max_r + 50
        lx = cx + label_r * math.cos(angle)
        ly = cy + label_r * math.sin(angle)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 13)
        lines = labels[i].split('\n')
        for li, line in enumerate(lines):
            c.drawCentredString(lx, ly - 5 - li * 16, line)

    # Draw polygons
    def draw_poly(data, fill_color, stroke_color):
        pts = []
        for i, val in enumerate(data):
            angle = math.radians(90 - i * (360 / n_axes))
            r = max_r * val
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        p.close()
        c.saveState()
        c.setFillColor(fill_color)
        c.setFillAlpha(0.20)
        c.setStrokeColor(stroke_color)
        c.setLineWidth(2.5)
        c.drawPath(p, stroke=1, fill=1)
        c.restoreState()
        # Dots
        for x, y in pts:
            c.setFillColor(stroke_color)
            c.circle(x, y, 5, stroke=0, fill=1)

    draw_poly(typical, BRICK, BRICK)
    draw_poly(optimized, EMERALD, EMERALD)

    # Legend
    legend_y = 100
    c.setFillColor(BRICK)
    c.circle(580, legend_y, 8, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    c.drawString(595, legend_y - 5, "Typical Enterprise Deployment")

    c.setFillColor(EMERALD)
    c.circle(860, legend_y, 8, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.drawString(875, legend_y - 5, "Optimized Deployment")


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
