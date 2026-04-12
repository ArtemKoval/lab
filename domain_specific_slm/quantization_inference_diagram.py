#!/usr/bin/env python3
"""
CAIO Diagram: Quantization Technique Comparison — GPTQ vs AWQ vs GGUF
Topic: quantization-inference
Type: Radar / spider chart overlay (3 series)
Output: caio-quantization-inference-diagram-1.png
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
TERRACOTTA = HexColor('#C4613A')
BRONZE = HexColor('#8C6E3A')

# --- Font Registration ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-quantization-inference-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 60, "Quantization Technique Comparison")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 90, "GPTQ vs AWQ vs GGUF across key deployment dimensions")

    # Radar chart
    cx, cy = W / 2, 530
    max_r = 300

    axes = [
        "GPU\nThroughput",
        "CPU\nPerformance",
        "Accuracy\nRetention",
        "Memory\nSavings",
        "Ecosystem\nSupport",
        "Deployment\nFlexibility",
    ]
    n = len(axes)

    # Grid rings
    for ring_pct in [0.2, 0.4, 0.6, 0.8, 1.0]:
        r = max_r * ring_pct
        c.setStrokeColor(HexColor('#E0E0E0'))
        c.setLineWidth(0.8)
        p = c.beginPath()
        for i in range(n + 1):
            ang = math.radians(90 - (i % n) * (360 / n))
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        c.drawPath(p, stroke=1, fill=0)

    # Axis lines and labels
    for i, label in enumerate(axes):
        ang = math.radians(90 - i * (360 / n))
        x_end = cx + max_r * math.cos(ang)
        y_end = cy + max_r * math.sin(ang)
        c.setStrokeColor(HexColor('#CCCCCC'))
        c.setLineWidth(1)
        c.line(cx, cy, x_end, y_end)

        # Labels
        lx = cx + (max_r + 55) * math.cos(ang)
        ly = cy + (max_r + 55) * math.sin(ang)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 14)
        label_lines = label.split('\n')
        for j, ll in enumerate(label_lines):
            c.drawCentredString(lx, ly - 5 - j * 18, ll)

    # Data series (normalized 0-1)
    series = [
        ("GPTQ", [0.95, 0.2, 0.92, 0.95, 0.85, 0.5], EMERALD),
        ("AWQ", [0.98, 0.15, 0.96, 0.95, 0.8, 0.45], BURGUNDY),
        ("GGUF", [0.5, 0.95, 0.88, 0.9, 0.9, 0.98], SAPPHIRE),
    ]

    for name, data, color in series:
        points = []
        for i, val in enumerate(data):
            ang = math.radians(90 - i * (360 / n))
            r = max_r * val
            points.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))

        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, y)
        p.close()

        c.setFillAlpha(0.18)
        c.setFillColor(color)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        c.drawPath(p, stroke=1, fill=1)
        c.setFillAlpha(1.0)

        # Dots at vertices
        for x, y in points:
            c.setFillColor(color)
            c.circle(x, y, 5, stroke=0, fill=1)

    # Legend
    legend_x = 200
    legend_y = 95
    for i, (name, _, color) in enumerate(series):
        lx = legend_x + i * 400
        c.setFillColor(color)
        c.circle(lx, legend_y, 10, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 16)
        c.drawString(lx + 18, legend_y - 6, name)

    # Insight note
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(
        W / 2, 55, "GPTQ and AWQ excel on GPU throughput — GGUF leads on CPU flexibility and cross-platform deployment")


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
