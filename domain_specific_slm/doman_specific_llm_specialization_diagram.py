#!/usr/bin/env python3
"""
CAIO Diagram: The Enterprise AI Architecture Stack
Topic: small-model-specialization
Type: Concentric rings
Output: caio-small-model-specialization-diagram-3.png
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
WHITE = HexColor('#FFFFFF')

pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-small-model-specialization-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'


def draw_diagram(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W/2, H - 60, "The Enterprise AI Architecture Stack")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W/2, H - 90, "From infrastructure outward to business value — specialization at every layer")

    cx, cy = W/2, 520

    rings = [
        (420, HexColor('#E8E0D0'), NAVY, "Business Value Layer",
         "Revenue impact — cost savings — competitive differentiation"),
        (340, TEAL, IVORY, "Deployment Layer",
         "On-premise — private cloud — edge — API gateway"),
        (260, AMETHYST, IVORY, "Evaluation Layer",
         "Syntax — static analysis — execution — domain validation"),
        (180, EMERALD, IVORY, "Fine-Tuning Layer",
         "LoRA — QLoRA — full fine-tuning — hyperparameter search"),
        (100, SAPPHIRE, IVORY, "Data Curation Layer",
         "Domain-specific — curated — quality over quantity"),
    ]

    for r, fill_color, text_color, title, desc in rings:
        c.setFillColor(fill_color)
        c.circle(cx, cy, r, stroke=0, fill=1)
        c.setStrokeColor(WHITE)
        c.setLineWidth(3)
        c.circle(cx, cy, r, stroke=1, fill=0)

    # Labels — placed at ring midpoints
    label_positions = [
        (380, rings[0]),
        (300, rings[1]),
        (220, rings[2]),
        (140, rings[3]),
    ]

    for mid_r, (_, _, text_color, title, desc) in label_positions:
        # Place label at right side of ring
        c.setFillColor(text_color)
        c.setFont('Poppins-Bold', 14)
        c.drawCentredString(cx, cy + mid_r - 5, title)
        c.setFont('Poppins', 10)
        c.drawCentredString(cx, cy + mid_r - 22, desc)

    # Innermost ring label
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 14)
    c.drawCentredString(cx, cy + 15, "Data Curation")
    c.setFont('Poppins', 10)
    c.drawCentredString(cx, cy - 5, "Domain-specific")
    c.drawCentredString(cx, cy - 20, "Quality over quantity")

    # Arrow labels on sides
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 13)
    # Left side: "Increasing Specialization →"
    c.saveState()
    c.translate(60, cy)
    c.rotate(90)
    c.drawCentredString(0, 0, "Increasing Specialization")
    c.restoreState()

    # Right side: "← Increasing Business Impact"
    c.saveState()
    c.translate(W - 60, cy)
    c.rotate(-90)
    c.drawCentredString(0, 0, "Increasing Business Impact")
    c.restoreState()


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    import subprocess
    subprocess.run(['pdftoppm', '-png', '-r', '150', '-singlefile',
                   OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
