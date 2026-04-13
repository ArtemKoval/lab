#!/usr/bin/env python3
"""
CAIO Diagram: SLM vs LLM Capability Comparison
Topic: coding-slms
Type: Radar Overlay
Output: caio-coding-slms-diagram-2.png
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
WARM_BLUE = HexColor('#2A5A8A')

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
OUTPUT_PNG = '/home/claude/caio-coding-slms-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    """Radar overlay comparing SLM vs LLM across enterprise dimensions."""
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(
        W/2, H - 60, "SLM vs LLM — Enterprise Capability Profile")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 90, "Comparing small specialized models against large general-purpose models for coding tasks")

    cx, cy = W/2, 540
    max_r = 300

    dimensions = [
        "Code Quality\n(Focused Tasks)",
        "Inference\nCost",
        "Data\nSovereignty",
        "Deployment\nFlexibility",
        "Fine-Tuning\nFeasibility",
        "Latency",
        "General\nReasoning",
        "Multi-Domain\nCapability",
    ]
    n = len(dimensions)

    # SLM scores (0-1, higher = better)
    slm_scores = [0.88, 0.95, 0.95, 0.90, 0.92, 0.95, 0.40, 0.30]
    # LLM scores (0-1, higher = better)
    llm_scores = [0.92, 0.20, 0.30, 0.40, 0.25, 0.45, 0.95, 0.95]

    # Grid lines
    for level in [0.25, 0.5, 0.75, 1.0]:
        r = max_r * level
        points = []
        for i in range(n):
            angle = math.radians(90 - i * (360 / n))
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        c.setStrokeColor(HexColor('#E0E0E0'))
        c.setLineWidth(0.5)
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for pt in points[1:]:
            p.lineTo(pt[0], pt[1])
        p.close()
        c.drawPath(p, stroke=1, fill=0)

        # Level label
        if level < 1.0:
            c.setFillColor(HexColor('#AAAAAA'))
            c.setFont('Poppins-Light', 9)
            c.drawString(cx + 4, cy + r + 2, f"{int(level*100)}%")

    # Spokes
    c.setStrokeColor(HexColor('#D0D0D0'))
    c.setLineWidth(1)
    for i in range(n):
        angle = math.radians(90 - i * (360 / n))
        x2 = cx + max_r * math.cos(angle)
        y2 = cy + max_r * math.sin(angle)
        c.line(cx, cy, x2, y2)

    # SLM polygon (Emerald)
    slm_points = []
    for i, score in enumerate(slm_scores):
        angle = math.radians(90 - i * (360 / n))
        r = max_r * score
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        slm_points.append((x, y))

    p = c.beginPath()
    p.moveTo(slm_points[0][0], slm_points[0][1])
    for pt in slm_points[1:]:
        p.lineTo(pt[0], pt[1])
    p.close()
    c.setFillColor(EMERALD)
    c.setFillAlpha(0.2)
    c.setStrokeColor(EMERALD)
    c.setLineWidth(3)
    c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1.0)

    # Score dots for SLM
    for x, y in slm_points:
        c.setFillColor(EMERALD)
        c.circle(x, y, 5, stroke=0, fill=1)

    # LLM polygon (Burgundy)
    llm_points = []
    for i, score in enumerate(llm_scores):
        angle = math.radians(90 - i * (360 / n))
        r = max_r * score
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        llm_points.append((x, y))

    p = c.beginPath()
    p.moveTo(llm_points[0][0], llm_points[0][1])
    for pt in llm_points[1:]:
        p.lineTo(pt[0], pt[1])
    p.close()
    c.setFillColor(BURGUNDY)
    c.setFillAlpha(0.2)
    c.setStrokeColor(BURGUNDY)
    c.setLineWidth(3)
    c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1.0)

    # Score dots for LLM
    for x, y in llm_points:
        c.setFillColor(BURGUNDY)
        c.circle(x, y, 5, stroke=0, fill=1)

    # Axis labels
    c.setFont('Poppins-Medium', 13)
    for i, label in enumerate(dimensions):
        angle = math.radians(90 - i * (360 / n))
        lx = cx + (max_r + 60) * math.cos(angle)
        ly = cy + (max_r + 60) * math.sin(angle)
        c.setFillColor(NAVY)
        lines = label.split('\n')
        for j, line in enumerate(lines):
            c.drawCentredString(lx, ly - j * 16, line)

    # Legend
    legend_y = 80
    # SLM
    c.setFillColor(EMERALD)
    c.rect(W/2 - 250, legend_y - 3, 20, 14, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 14)
    c.drawString(W/2 - 224, legend_y,
                 "Specialized SLM (3-7B, quantized, local)")
    # LLM
    c.setFillColor(BURGUNDY)
    c.rect(W/2 - 250, legend_y - 30, 20, 14, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.drawString(W/2 - 224, legend_y - 27,
                 "Frontier LLM (100B+, cloud-hosted)")

    # Bottom note
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(
        W/2, 30, "SLMs dominate on cost, sovereignty, latency, and fine-tuning — LLMs lead on general reasoning and multi-domain breadth")


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
