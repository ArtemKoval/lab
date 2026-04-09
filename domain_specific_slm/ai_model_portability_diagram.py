#!/usr/bin/env python3
"""
CAIO Diagram: Enterprise AI Deployment Maturity
Topic: model-portability
Type: Concentric rings
Output: caio-model-portability-diagram-3.png
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
WARM_BLUE = HexColor('#2A5A8A')

pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-model-portability-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W/2, H - 60, "Enterprise AI Deployment Maturity")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 90, "From single-framework to hardware-agnostic deployment")

    cx, cy = W/2, 520

    # Rings from outermost to innermost
    rings = [
        (400, "Edge-Native, Hardware-Agnostic Deployment", EMERALD,
         "Models run on any device — NPUs, ARM, x86 — via configuration, not code changes"),
        (310, "Multi-Target Serving Infrastructure", TEAL,
         "Single model serves multiple hardware targets through execution providers"),
        (220, "Portable Format Adoption (ONNX)", AMETHYST,
         "Models exported to open standard format, decoupled from training framework"),
        (130, "Single-Framework Deployment", BURGUNDY,
         "Models tied to training framework runtime — PyTorch Serve, TF Serving"),
    ]

    for r, title, color, desc in rings:
        c.setFillColor(color)
        c.circle(cx, cy, r, stroke=0, fill=1)
        # White ring border
        c.setStrokeColor(HexColor('#FFFFFF'))
        c.setLineWidth(4)
        c.circle(cx, cy, r, stroke=1, fill=0)

    # Labels — placed to the right of each ring with leader lines
    label_x = cx + 420
    c.setLineWidth(1.5)

    label_data = [
        (400, rings[0][1], rings[0][3], rings[0][2], 85),
        (310, rings[1][1], rings[1][3], rings[1][2], 70),
        (220, rings[2][1], rings[2][3], rings[2][2], 45),
        (130, rings[3][1], rings[3][3], rings[3][2], 20),
    ]

    for i, (r, title, desc, color, angle_deg) in enumerate(label_data):
        # Point on ring
        angle = math.radians(angle_deg)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)

        # Label position
        ly = cy + 280 - i * 155
        lx = label_x

        # Leader line
        c.setStrokeColor(GRAPHITE)
        c.setLineWidth(1)
        c.line(px, py, lx - 10, ly + 8)

        # Small circle marker
        c.setFillColor(color)
        c.circle(lx - 20, ly + 8, 6, stroke=0, fill=1)

        # Title
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 14)
        c.drawString(lx, ly + 4, title)

        # Description
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins-Light', 11)
        # Wrap description
        words = desc.split()
        lines = []
        current = ""
        for w in words:
            test = current + " " + w if current else w
            if c.stringWidth(test, 'Poppins-Light', 11) <= 380:
                current = test
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
        for j, line in enumerate(lines):
            c.drawString(lx, ly - 14 - j * 14, line)

    # Center label
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(cx, cy + 10, "Single")
    c.drawCentredString(cx, cy - 10, "Framework")

    # Bottom annotation
    c.setFillColor(OCHRE)
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(cx - 200, 80, "Core (most constrained)")
    c.setFillColor(EMERALD)
    c.drawCentredString(cx + 200, 80, "Edge (most portable)")

    # Arrow arc from left to right
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(2)
    c.setDash(6, 4)
    p = c.beginPath()
    p.arc(cx - 300, 60, cx + 300, 120, 180, -180)
    c.drawPath(p, stroke=1, fill=0)
    c.setDash()


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
