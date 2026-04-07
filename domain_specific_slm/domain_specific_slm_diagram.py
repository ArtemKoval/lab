#!/usr/bin/env python3
"""
CAIO Diagram: SLM vs LLM Enterprise Capability Radar
Topic: domain-specific-slms
Type: Radar / Spider Chart Overlay
Output: caio-domain-specific-slms-diagram-1.png
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

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-domain-specific-slms-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    """Radar chart comparing SLM vs LLM across enterprise dimensions."""
    # Background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(
        W/2, H - 60, 'SLM vs LLM — Enterprise Capability Profile')

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 90, 'Comparative assessment across six operational dimensions')

    # Radar parameters
    cx, cy = W/2, H/2 - 30
    max_r = 340
    n_axes = 7
    dimensions = [
        'Domain\nPrecision',
        'Data\nPrivacy',
        'Inference\nCost',
        'Deployment\nFlexibility',
        'Latency',
        'Governance\nControl',
        'Creative\nBreadth'
    ]

    # Scores (0-100 scale)
    # SLMs strong on precision/privacy/cost
    slm_scores = [92, 95, 88, 90, 93, 91, 35]
    llm_scores = [55, 40, 30, 45, 40, 35, 95]   # LLMs strong on breadth

    # Draw grid rings
    for ring_pct in [0.2, 0.4, 0.6, 0.8, 1.0]:
        r = max_r * ring_pct
        p = c.beginPath()
        for i in range(n_axes):
            angle = math.radians(90 - i * (360 / n_axes))
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        p.close()
        c.setStrokeColor(HexColor('#D0D0D0'))
        c.setLineWidth(0.8)
        c.drawPath(p, stroke=1, fill=0)

    # Draw axis lines
    for i in range(n_axes):
        angle = math.radians(90 - i * (360 / n_axes))
        x = cx + max_r * math.cos(angle)
        y = cy + max_r * math.sin(angle)
        c.setStrokeColor(HexColor('#C0C0C0'))
        c.setLineWidth(0.5)
        c.line(cx, cy, x, y)

    # Draw SLM polygon
    slm_points = []
    for i, score in enumerate(slm_scores):
        angle = math.radians(90 - i * (360 / n_axes))
        r = max_r * (score / 100)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        slm_points.append((x, y))

    p = c.beginPath()
    p.moveTo(slm_points[0][0], slm_points[0][1])
    for x, y in slm_points[1:]:
        p.lineTo(x, y)
    p.close()
    c.saveState()
    c.setFillColor(EMERALD)
    c.setFillAlpha(0.25)
    c.setStrokeColor(EMERALD)
    c.setLineWidth(2.5)
    c.drawPath(p, stroke=1, fill=1)
    c.restoreState()

    # Draw LLM polygon
    llm_points = []
    for i, score in enumerate(llm_scores):
        angle = math.radians(90 - i * (360 / n_axes))
        r = max_r * (score / 100)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        llm_points.append((x, y))

    p = c.beginPath()
    p.moveTo(llm_points[0][0], llm_points[0][1])
    for x, y in llm_points[1:]:
        p.lineTo(x, y)
    p.close()
    c.saveState()
    c.setFillColor(BURGUNDY)
    c.setFillAlpha(0.2)
    c.setStrokeColor(BURGUNDY)
    c.setLineWidth(2.5)
    c.drawPath(p, stroke=1, fill=1)
    c.restoreState()

    # Draw dots at data points
    for x, y in slm_points:
        c.setFillColor(EMERALD)
        c.circle(x, y, 5, stroke=0, fill=1)
    for x, y in llm_points:
        c.setFillColor(BURGUNDY)
        c.circle(x, y, 5, stroke=0, fill=1)

    # Axis labels
    label_margin = 50
    for i, label in enumerate(dimensions):
        angle = math.radians(90 - i * (360 / n_axes))
        lx = cx + (max_r + label_margin) * math.cos(angle)
        ly = cy + (max_r + label_margin) * math.sin(angle)

        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 14)
        lines = label.split('\n')
        for li, line in enumerate(lines):
            c.drawCentredString(lx, ly - li * 18, line)

    # Legend
    legend_x = W - 320
    legend_y = 120

    c.setFillColor(EMERALD)
    c.circle(legend_x, legend_y + 4, 8, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawString(legend_x + 16, legend_y - 4, 'Domain-Specific SLM')

    c.setFillColor(BURGUNDY)
    c.circle(legend_x, legend_y - 30 + 4, 8, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.drawString(legend_x + 16, legend_y - 30 - 4, 'General-Purpose LLM')


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
