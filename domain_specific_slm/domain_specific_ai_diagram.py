#!/usr/bin/env python3
"""
CAIO Diagram: RAG vs Fine-Tuning vs PEFT — Capability Profile
Topic: domain-specific-ai
Type: Radar / Spider Overlay
Output: caio-domain-specific-ai-diagram-2.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')

# --- Fonts ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-domain-specific-ai-diagram-2.png'
OUTPUT_PDF = '/tmp/_diagram2_temp.pdf'


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W/2, H - 60, "RAG vs Fine-Tuning vs PEFT")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 90, "Capability profile across eight enterprise dimensions")

    cx, cy = W/2, 530
    max_r = 280

    dims = [
        "Cost\nEfficiency",
        "Data\nFreshness",
        "Source\nTraceability",
        "Behavioral\nConsistency",
        "Domain\nDepth",
        "Setup\nSpeed",
        "ML Expertise\nRequired (inv.)",
        "Governance\nReadiness",
    ]
    n = len(dims)

    # Scores (0-1)
    rag_scores = [0.90, 0.95, 0.95, 0.35, 0.45, 0.85, 0.80, 0.90]
    ft_scores = [0.20, 0.25, 0.15, 0.90, 0.95, 0.25, 0.20, 0.50]
    peft_scores = [0.70, 0.30, 0.20, 0.80, 0.80, 0.65, 0.55, 0.55]

    series = [
        (rag_scores, EMERALD, "RAG"),
        (ft_scores, BURGUNDY, "Fine-Tuning"),
        (peft_scores, AMETHYST, "PEFT / LoRA"),
    ]

    # Grid rings
    for ring_val in [0.25, 0.5, 0.75, 1.0]:
        r = max_r * ring_val
        c.setStrokeColor(HexColor('#E0E0E0'))
        c.setLineWidth(0.5)
        p = c.beginPath()
        for i in range(n):
            angle = math.radians(90 - i * (360 / n))
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    # Spokes and labels
    for i, dim in enumerate(dims):
        angle = math.radians(90 - i * (360 / n))
        x_end = cx + max_r * math.cos(angle)
        y_end = cy + max_r * math.sin(angle)
        c.setStrokeColor(HexColor('#D0D0D0'))
        c.setLineWidth(0.5)
        c.line(cx, cy, x_end, y_end)

        lx = cx + (max_r + 50) * math.cos(angle)
        ly = cy + (max_r + 50) * math.sin(angle)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 12)
        for j, line in enumerate(dim.split('\n')):
            c.drawCentredString(lx, ly - 6 - j * 16, line)

    # Draw polygons
    for scores, color, label in series:
        points = []
        for i, s in enumerate(scores):
            angle = math.radians(90 - i * (360 / n))
            r = max_r * s
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, y)
        p.close()
        c.saveState()
        c.setFillAlpha(0.18)
        c.setFillColor(color)
        c.setStrokeColor(color)
        c.setLineWidth(2.5)
        c.drawPath(p, stroke=1, fill=1)
        c.restoreState()

        # Dot markers
        for x, y in points:
            c.setFillColor(color)
            c.circle(x, y, 5, stroke=0, fill=1)

    # Legend
    legend_y = 80
    legend_x = W/2 - 200
    for i, (_, color, label) in enumerate(series):
        lx = legend_x + i * 180
        c.setFillColor(color)
        c.circle(lx, legend_y + 5, 8, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins', 14)
        c.drawString(lx + 16, legend_y, label)


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
