#!/usr/bin/env python3
"""
CAIO Diagram: Frontier API vs Domain-Trained SLM — Multi-Dimension Profile
Topic: caio-reasoning-at-inference
Type: Radar overlay (two profiles across 6 strategic dimensions)
Output: caio-reasoning-at-inference-diagram-2.png
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
TERRACOTTA = HexColor('#C4613A')

pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-reasoning-at-inference-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W / 2, H - 70, "Frontier API vs Domain-Trained SLM")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(
        W / 2, H - 100, "Strategic profile across six dimensions — scored 1 (low) to 5 (high)")

    # Radar center
    cx, cy = 750, 560
    max_r = 320

    # Dimensions (clockwise from top)
    dimensions = [
        "Reasoning quality\n(generic tasks)",
        "Domain accuracy",
        "Unit economics\n(at enterprise volume)",
        "Data residency control",
        "Deployment speed",
        "Explainability",
    ]
    n = len(dimensions)

    # Scores (1 = outer-low, 5 = outer-high, all scaled against a shared max)
    # Series 1: Frontier reasoning API (e.g., o3, Claude)
    # Strong: reasoning quality (generic), deployment speed
    # Weak: domain accuracy (no domain tuning), per-query cost (expensive), residency (data leaves), explainability (hidden thinking)
    frontier_api = [5, 2, 2, 2, 5, 2]
    # Series 2: Domain-trained SLM (GRPO + LoRA + local serving)
    # Strong: domain accuracy, per-query cost (local), residency (fully controlled), explainability (full traces)
    # Weak: generic reasoning (narrower), deployment speed (requires engineering)
    domain_slm = [3, 5, 5, 5, 3, 5]

    # Draw concentric grid polygons (5 rings)
    for ring in range(1, 6):
        r = max_r * (ring / 5)
        points = []
        for i in range(n):
            # Start from top (12 o'clock), go clockwise
            angle_deg = 90 - i * (360 / n)
            angle_rad = math.radians(angle_deg)
            x = cx + r * math.cos(angle_rad)
            y = cy + r * math.sin(angle_rad)
            points.append((x, y))
        c.setStrokeColor(HexColor('#D0D0D0'))
        c.setLineWidth(0.8)
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    # Draw axis spokes from center to each dimension
    for i in range(n):
        angle_deg = 90 - i * (360 / n)
        angle_rad = math.radians(angle_deg)
        x = cx + max_r * math.cos(angle_rad)
        y = cy + max_r * math.sin(angle_rad)
        c.setStrokeColor(HexColor('#C0C0C0'))
        c.setLineWidth(0.8)
        c.line(cx, cy, x, y)

    # Series 1: Frontier API (Burgundy)
    points1 = []
    for i, val in enumerate(frontier_api):
        angle_deg = 90 - i * (360 / n)
        angle_rad = math.radians(angle_deg)
        r = max_r * (val / 5)
        x = cx + r * math.cos(angle_rad)
        y = cy + r * math.sin(angle_rad)
        points1.append((x, y))

    c.setFillColor(BURGUNDY)
    c.setFillAlpha(0.3)
    c.setStrokeColor(BURGUNDY)
    c.setLineWidth(3)
    p = c.beginPath()
    p.moveTo(points1[0][0], points1[0][1])
    for x, y in points1[1:]:
        p.lineTo(x, y)
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1.0)

    # Draw markers at vertex points for series 1
    for x, y in points1:
        c.setFillColor(BURGUNDY)
        c.circle(x, y, 7, stroke=0, fill=1)

    # Series 2: Domain-trained SLM (Emerald)
    points2 = []
    for i, val in enumerate(domain_slm):
        angle_deg = 90 - i * (360 / n)
        angle_rad = math.radians(angle_deg)
        r = max_r * (val / 5)
        x = cx + r * math.cos(angle_rad)
        y = cy + r * math.sin(angle_rad)
        points2.append((x, y))

    c.setFillColor(EMERALD)
    c.setFillAlpha(0.3)
    c.setStrokeColor(EMERALD)
    c.setLineWidth(3)
    p = c.beginPath()
    p.moveTo(points2[0][0], points2[0][1])
    for x, y in points2[1:]:
        p.lineTo(x, y)
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1.0)

    for x, y in points2:
        c.setFillColor(EMERALD)
        c.circle(x, y, 7, stroke=0, fill=1)

    # Axis labels (outside the outermost ring)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 14)
    label_r = max_r + 55
    for i, dim in enumerate(dimensions):
        angle_deg = 90 - i * (360 / n)
        angle_rad = math.radians(angle_deg)
        lx = cx + label_r * math.cos(angle_rad)
        ly = cy + label_r * math.sin(angle_rad)
        # Multi-line labels handled manually
        lines = dim.split("\n")
        if len(lines) == 1:
            c.drawCentredString(lx, ly, lines[0])
        else:
            # First line higher, second line lower
            total_h = 18 * len(lines)
            for li, line in enumerate(lines):
                y_offset = (total_h / 2) - li * 18 - 9
                c.drawCentredString(lx, ly + y_offset, line)

    # Legend (top right)
    legend_x = 1270
    legend_y = H - 180
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 15)
    c.drawString(legend_x, legend_y, "Legend")

    # Frontier API entry
    c.setFillColor(BURGUNDY)
    c.circle(legend_x + 12, legend_y - 30, 10, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawString(legend_x + 32, legend_y - 34, "Frontier reasoning API")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)
    c.drawString(legend_x + 32, legend_y - 52, "o-series, Claude, Gemini")

    # Domain-trained SLM entry
    c.setFillColor(EMERALD)
    c.circle(legend_x + 12, legend_y - 90, 10, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawString(legend_x + 32, legend_y - 94, "Domain-trained SLM")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)
    c.drawString(legend_x + 32, legend_y - 112, "GRPO + LoRA on local GPU")

    # Key takeaway box
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawString(legend_x, legend_y - 170, "Read the shape.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)
    c.drawString(legend_x, legend_y - 190, "Frontier API wins on")
    c.drawString(legend_x, legend_y - 206, "generic reasoning and")
    c.drawString(legend_x, legend_y - 222, "speed to deploy.")
    c.drawString(legend_x, legend_y - 246, "Domain SLM wins on")
    c.drawString(legend_x, legend_y - 262, "everything that matters")
    c.drawString(legend_x, legend_y - 278, "at enterprise volume.")

    # Footer
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(
        W / 2, 40, "Scoring derived from AWS 2026 fine-tuning analysis, Hugging Face test-time scaling research, and Iternal AI April 2026 pricing analysis")


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
