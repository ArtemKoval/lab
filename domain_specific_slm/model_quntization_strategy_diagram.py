#!/usr/bin/env python3
"""
CAIO Diagram: The Precision-Deployment Matrix
Topic: quantization-strategy
Type: Concentric rings
Output: caio-quantization-strategy-diagram-1.png
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
OUTPUT_PNG = '/home/claude/caio-quantization-strategy-diagram-1.png'
OUTPUT_PDF = '/tmp/_diagram1_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFont('Poppins-Bold', 32)
    c.setFillColor(NAVY)
    c.drawCentredString(W/2, H - 70, "The Precision-Deployment Matrix")

    c.setFont('Poppins-Light', 16)
    c.setFillColor(GRAPHITE)
    c.drawCentredString(
        W/2, H - 100, "Mapping Quantization Levels to Infrastructure Targets")

    cx, cy = W/2, 530

    # Outer ring: 4-bit (edge/mobile)
    c.setFillColor(HexColor('#E8F5E9'))  # Light green
    c.circle(cx, cy, 350, stroke=0, fill=1)
    c.setStrokeColor(EMERALD)
    c.setLineWidth(3)
    c.circle(cx, cy, 350, stroke=1, fill=0)

    # Middle ring: 8-bit (production)
    c.setFillColor(HexColor('#E3F2FD'))  # Light blue
    c.circle(cx, cy, 240, stroke=0, fill=1)
    c.setStrokeColor(SAPPHIRE)
    c.setLineWidth(3)
    c.circle(cx, cy, 240, stroke=1, fill=0)

    # Inner ring: FP16/32 (cloud)
    c.setFillColor(HexColor('#FFF3E0'))  # Light amber
    c.circle(cx, cy, 130, stroke=0, fill=1)
    c.setStrokeColor(OCHRE)
    c.setLineWidth(3)
    c.circle(cx, cy, 130, stroke=1, fill=0)

    # Center label
    c.setFont('Poppins-Bold', 22)
    c.setFillColor(NAVY)
    c.drawCentredString(cx, cy + 30, "FP16 / FP32")
    c.setFont('Poppins-Medium', 14)
    c.setFillColor(GRAPHITE)
    c.drawCentredString(cx, cy + 8, "Cloud GPU Clusters")
    c.setFont('Poppins', 12)
    c.drawCentredString(cx, cy - 12, "Frontier reasoning")
    c.drawCentredString(cx, cy - 28, "Safety-critical decisions")
    c.drawCentredString(cx, cy - 44, "Multi-step analysis")

    # Middle ring labels — at 3 o'clock and 9 o'clock
    c.setFont('Poppins-Bold', 18)
    c.setFillColor(SAPPHIRE)
    c.drawCentredString(cx, cy + 200, "INT8 — Production Servers")
    c.setFont('Poppins', 13)
    c.setFillColor(GRAPHITE)
    c.drawCentredString(
        cx, cy + 180, "APIs, batch processing, document analysis")
    c.drawCentredString(cx, cy + 162, "2x memory reduction, ~99% quality")

    # Outer ring labels — top and bottom
    c.setFont('Poppins-Bold', 18)
    c.setFillColor(EMERALD)
    c.drawCentredString(cx, cy - 280, "INT4 / NF4 — Edge, Mobile, Laptop")
    c.setFont('Poppins', 13)
    c.setFillColor(GRAPHITE)
    c.drawCentredString(
        cx, cy - 300, "Offline inference, privacy-sensitive tasks")
    c.drawCentredString(
        cx, cy - 318, "4x memory reduction, ~95% quality, zero serving cost")

    # Use case examples positioned around the rings
    examples = [
        # Outer ring examples (4-bit)
        (cx - 280, cy + 280, "Mobile AI\nassistant", EMERALD),
        (cx + 280, cy + 280, "Retail edge\nserver", EMERALD),
        (cx - 340, cy - 50, "IoT sensor\nprocessing", EMERALD),
        (cx + 340, cy - 50, "Offline\ndocument QA", EMERALD),
        # Middle ring examples (8-bit)
        (cx - 180, cy - 170, "Customer\nsupport API", SAPPHIRE),
        (cx + 180, cy - 170, "Code\nassistant", SAPPHIRE),
    ]

    for ex, ey, label, color in examples:
        c.setFillColor(color)
        c.circle(ex, ey, 40, stroke=0, fill=1)
        c.setFont('Poppins-Bold', 10)
        c.setFillColor(IVORY)
        lines = label.split('\n')
        for j, line in enumerate(lines):
            c.drawCentredString(ex, ey + 5 - j * 14, line)

    # Cost arrow annotation
    c.setFont('Poppins-Medium', 14)
    c.setFillColor(NAVY)
    c.drawString(80, 130, "Center = highest cost, highest precision")
    c.drawString(80, 108, "Edge = lowest cost, broadest deployment")


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
