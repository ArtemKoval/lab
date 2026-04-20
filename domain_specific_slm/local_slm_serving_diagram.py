#!/usr/bin/env python3
"""
CAIO Diagram: The Laptop-Native Inference Stack — A Three-Way Capability Overlay
Topic: laptop-native-ai
Type: Radar / spider chart overlay with three series (Ollama, LM Studio, Jan)
Output: caio-laptop-native-ai-diagram-2.png
"""

import math
import subprocess
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
TERRACOTTA = HexColor('#C4613A')
WHITE = HexColor('#FFFFFF')

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
OUTPUT_PNG = '/home/claude/caio-laptop-native-ai-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(
        W / 2, H - 80, "The Three Credible Laptop-Native Inference Stacks")

    # Subtitle
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, H - 115, "Capability overlay across seven enterprise-relevant dimensions")

    # Axes definitions — 7 dimensions
    dimensions = [
        "Open source\nlicensing",
        "Graphical\ninterface quality",
        "REST API\nmaturity",
        "Model format\nbreadth",
        "Inference\nperformance",
        "SDK\nproductization",
        "Cloud-local\nrouting",
    ]

    # Scores 0-5 for each dimension (qualitative judgment based on source material)
    # Order must match dimensions
    series = [
        ("Ollama", [5, 2, 5, 4, 4, 5, 3], EMERALD),
        ("LM Studio", [2, 5, 5, 5, 5, 5, 2], BURGUNDY),
        ("Jan", [5, 4, 5, 3, 3, 2, 5], AMETHYST),
    ]

    cx, cy = W / 2, 560
    max_r = 300
    max_val = 5
    n = len(dimensions)

    # --- Draw concentric gridlines (polygons) ---
    for ring_val in [1, 2, 3, 4, 5]:
        r = max_r * (ring_val / max_val)
        points = []
        for i in range(n):
            angle = math.radians(90 - i * (360 / n))
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))

        c.setStrokeColor(HexColor('#D0D0D0'))
        c.setLineWidth(1)
        c.setFillColor(WHITE)
        c.setFillAlpha(0)
        path = c.beginPath()
        path.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            path.lineTo(x, y)
        path.close()
        c.drawPath(path, stroke=1, fill=0)

    # --- Draw axis spokes ---
    c.setStrokeColor(HexColor('#C0C0C0'))
    c.setLineWidth(1)
    for i in range(n):
        angle = math.radians(90 - i * (360 / n))
        x = cx + max_r * math.cos(angle)
        y = cy + max_r * math.sin(angle)
        c.line(cx, cy, x, y)

    # --- Draw each series polygon ---
    for name, values, color in series:
        points = []
        for i, value in enumerate(values):
            angle = math.radians(90 - i * (360 / n))
            r = max_r * (value / max_val)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))

        # Filled polygon (semi-transparent)
        c.setFillColor(color)
        c.setFillAlpha(0.22)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        path = c.beginPath()
        path.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            path.lineTo(x, y)
        path.close()
        c.drawPath(path, stroke=1, fill=1)
        c.setFillAlpha(1.0)

        # Vertex dots
        c.setFillColor(color)
        for x, y in points:
            c.circle(x, y, 4, stroke=0, fill=1)

    # --- Axis labels ---
    c.setFillColor(NAVY)
    for i, dim in enumerate(dimensions):
        angle = math.radians(90 - i * (360 / n))
        label_r = max_r + 55
        lx = cx + label_r * math.cos(angle)
        ly = cy + label_r * math.sin(angle)

        lines = dim.split("\n")
        c.setFont('Poppins-Medium', 13)
        for idx, line in enumerate(lines):
            c.drawCentredString(lx, ly + 8 - idx * 16, line)

    # --- Legend (bottom) ---
    legend_y = 140
    legend_x_start = W / 2 - 380
    col_width = 260
    for idx, (name, _, color) in enumerate(series):
        lx = legend_x_start + idx * col_width
        # Filled swatch
        c.setFillColor(color)
        c.setFillAlpha(0.45)
        c.rect(lx, legend_y - 4, 30, 18, stroke=0, fill=1)
        c.setFillAlpha(1.0)
        c.setStrokeColor(color)
        c.setLineWidth(2)
        c.rect(lx, legend_y - 4, 30, 18, stroke=1, fill=0)
        # Label
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 16)
        c.drawString(lx + 40, legend_y, name)

    # Attribution
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 90,
                        "Capability scoring based on official project documentation and feature parity as of April 2026")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()

    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF,
        OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
