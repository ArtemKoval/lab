#!/usr/bin/env python3
"""
CAIO Diagram: Advanced Quantization Techniques — Capability Comparison
Topic: advanced-quantization
Type: Radar/Spider Overlay (3 series)
Output: caio-advanced-quantization-diagram-2.png
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
WHITE = HexColor('#FFFFFF')
LIGHT_GRAY = HexColor('#E0E0E0')

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
OUTPUT_PNG = '/home/claude/caio-advanced-quantization-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    """Main diagram drawing function."""
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(
        W/2, H - 60, "Advanced Quantization — Capability Profiles")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 90, "Comparing FlexGen, SmoothQuant, and BitNet across six enterprise dimensions")

    # Radar setup
    cx, cy = W/2, H/2 - 20
    max_r = 340

    # 6 axes
    axes = [
        "Accuracy\nPreservation",
        "Memory\nReduction",
        "Inference\nSpeed",
        "Energy\nEfficiency",
        "Deployment\nFlexibility",
        "Implementation\nSimplicity",
    ]
    n_axes = len(axes)

    # Data (0-100 scale)
    # FlexGen: great memory reduction, OK accuracy, slow latency, moderate energy, moderate flexibility, moderate simplicity
    # SmoothQuant: excellent accuracy, good memory, good speed, good energy, moderate flexibility, good simplicity
    # BitNet: good accuracy, excellent memory, excellent speed, excellent energy, excellent flexibility, low simplicity (needs from-scratch training)
    series = [
        {"name": "SmoothQuant", "color": EMERALD,
            "values": [95, 60, 70, 65, 50, 75]},
        {"name": "FlexGen", "color": SAPPHIRE,
            "values": [85, 90, 30, 45, 60, 55]},
        {"name": "BitNet", "color": AMETHYST,
            "values": [80, 95, 90, 95, 90, 25]},
    ]

    # Draw gridlines (concentric polygons at 20, 40, 60, 80, 100)
    grid_levels = [20, 40, 60, 80, 100]
    for level in grid_levels:
        r = max_r * level / 100
        points = []
        for i in range(n_axes):
            angle = math.radians(90 - i * (360 / n_axes))
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        # Draw polygon
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, y)
        p.close()
        c.setStrokeColor(LIGHT_GRAY)
        c.setLineWidth(1)
        c.drawPath(p, stroke=1, fill=0)

    # Draw spoke lines
    for i in range(n_axes):
        angle = math.radians(90 - i * (360 / n_axes))
        x2 = cx + max_r * math.cos(angle)
        y2 = cy + max_r * math.sin(angle)
        c.setStrokeColor(LIGHT_GRAY)
        c.setLineWidth(1)
        c.line(cx, cy, x2, y2)

    # Draw axis labels
    label_r = max_r + 55
    for i, label in enumerate(axes):
        angle = math.radians(90 - i * (360 / n_axes))
        lx = cx + label_r * math.cos(angle)
        ly = cy + label_r * math.sin(angle)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 14)
        lines = label.split('\n')
        for j, line in enumerate(lines):
            c.drawCentredString(lx, ly - j * 18 + 8, line)

    # Draw grid level labels on first spoke
    for level in grid_levels:
        r = max_r * level / 100
        angle = math.radians(90)
        lx = cx + r * math.cos(angle) + 18
        ly = cy + r * math.sin(angle) - 5
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 10)
        c.drawString(lx, ly, str(level))

    # Draw series polygons
    for series_data in series:
        points = []
        for i, value in enumerate(series_data['values']):
            angle = math.radians(90 - i * (360 / n_axes))
            r = max_r * value / 100
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))

        # Fill polygon
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, y)
        p.close()
        c.saveState()
        c.setFillAlpha(0.2)
        c.setFillColor(series_data['color'])
        c.setStrokeColor(series_data['color'])
        c.setLineWidth(2.5)
        c.drawPath(p, stroke=1, fill=1)
        c.restoreState()

        # Draw dots at vertices
        for x, y in points:
            c.setFillColor(series_data['color'])
            c.circle(x, y, 5, stroke=0, fill=1)

    # Legend
    legend_x = W - 280
    legend_y = H - 140
    for i, s in enumerate(series):
        ly = legend_y - i * 35
        c.setFillColor(s['color'])
        c.circle(legend_x, ly + 5, 8, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 16)
        c.drawString(legend_x + 18, ly - 2, s['name'])

    # Bottom attribution
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(
        W/2, 30, "Scores reflect enterprise deployment suitability — not raw benchmark performance")


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
