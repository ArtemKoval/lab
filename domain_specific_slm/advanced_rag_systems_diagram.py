#!/usr/bin/env python3
"""
CAIO Diagram: Baseline RAG vs Advanced RAG Capability Profile
Topic: advanced-rag-architectures
Type: Radar / spider overlay
Output: caio-advanced-rag-architectures-diagram-2.png
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
OUTPUT_PNG = '/home/claude/caio-advanced-rag-architectures-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    # Background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(
        W/2, H - 70, "Baseline RAG vs Advanced RAG — Capability Profile")

    # Subtitle
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 105, "Scored 0–10 across seven enterprise retrieval dimensions")

    # Radar center
    cx, cy = W/2, H/2 - 60
    max_r = 310
    n_rings = 5

    # Dimensions (7 axes, clockwise from top)
    dimensions = [
        "Multi-hop\nreasoning",
        "Global / thematic\nqueries",
        "Traceability\n& provenance",
        "Schema-bound\naccuracy",
        "Session\ncontinuity",
        "Adaptive\nretrieval",
        "Governance\nreadiness",
    ]
    n = len(dimensions)

    # Baseline RAG scores (0-10)
    baseline = [2, 2, 4, 1, 2, 2, 3]
    # Advanced RAG (Graph + Agentic + Memory) scores
    advanced = [9, 9, 8, 9, 8, 9, 8]

    # Draw concentric grid rings (circles)
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.setLineWidth(1)
    for ring in range(1, n_rings + 1):
        r = max_r * ring / n_rings
        c.circle(cx, cy, r, stroke=1, fill=0)

    # Ring value labels
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 10)
    for ring in range(1, n_rings + 1):
        r = max_r * ring / n_rings
        val = ring * 2  # 2, 4, 6, 8, 10
        c.drawString(cx + 4, cy + r - 4, str(val))

    # Draw spokes (axes)
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.setLineWidth(1)
    for i in range(n):
        angle = math.radians(90 - i * (360 / n))
        x_end = cx + max_r * math.cos(angle)
        y_end = cy + max_r * math.sin(angle)
        c.line(cx, cy, x_end, y_end)

    # Helper: draw filled polygon
    def draw_polygon(values, fill_color, stroke_color, alpha=0.30):
        points = []
        for i, v in enumerate(values):
            angle = math.radians(90 - i * (360 / n))
            r = max_r * (v / 10.0)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, y)
        p.close()
        c.setFillAlpha(alpha)
        c.setFillColor(fill_color)
        c.setStrokeColor(stroke_color)
        c.setLineWidth(3)
        c.drawPath(p, stroke=1, fill=1)
        c.setFillAlpha(1.0)
        # Draw value dots
        for x, y in points:
            c.setFillColor(stroke_color)
            c.circle(x, y, 5, stroke=0, fill=1)

    # Draw advanced polygon first (larger, in back), then baseline (smaller, on top)
    draw_polygon(advanced, EMERALD, EMERALD, 0.22)
    draw_polygon(baseline, BURGUNDY, BURGUNDY, 0.55)

    # Draw dimension labels at spoke tips (outside the chart)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 14)
    for i, label in enumerate(dimensions):
        angle = math.radians(90 - i * (360 / n))
        label_r = max_r + 55
        lx = cx + label_r * math.cos(angle)
        ly = cy + label_r * math.sin(angle)
        lines = label.split('\n')
        total_h = len(lines) * 18
        for j, line in enumerate(lines):
            c.drawCentredString(lx, ly + (total_h / 2 - 9) - j * 18, line)

    # Legend at bottom
    legend_y = 100
    # Baseline swatch
    c.setFillAlpha(0.28)
    c.setFillColor(BURGUNDY)
    c.setStrokeColor(BURGUNDY)
    c.setLineWidth(2)
    c.rect(cx - 340, legend_y - 15, 30, 20, stroke=1, fill=1)
    c.setFillAlpha(1.0)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawString(cx - 300, legend_y - 10, "Baseline RAG")
    c.setFont('Poppins', 13)
    c.setFillColor(GRAPHITE)
    c.drawString(cx - 300, legend_y - 32, "Vector search + chunk retrieval")

    # Advanced swatch
    c.setFillAlpha(0.28)
    c.setFillColor(EMERALD)
    c.setStrokeColor(EMERALD)
    c.setLineWidth(2)
    c.rect(cx + 60, legend_y - 15, 30, 20, stroke=1, fill=1)
    c.setFillAlpha(1.0)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawString(cx + 100, legend_y - 10, "Advanced RAG")
    c.setFont('Poppins', 13)
    c.setFillColor(GRAPHITE)
    c.drawString(cx + 100, legend_y - 32, "Graph + agentic + memory")

    # Attribution
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(W/2, 40, "Art Koval")


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
