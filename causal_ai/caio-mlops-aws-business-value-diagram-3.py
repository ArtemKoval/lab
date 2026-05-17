#!/usr/bin/env python3
"""
CAIO Diagram: MLOps Maturity as Business Capability
Topic: mlops-aws-business-value
Type: Concentric Rings
Output: caio-mlops-aws-business-value-diagram-3.png
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
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')
TAUPE = HexColor('#8A7B6B')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/caio-mlops-aws-business-value-diagram-3.png'
OUTPUT_PDF = '/tmp/_diag3_temp.pdf'


def draw_diagram(c):
    # White background
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W/2, H - 70, "MLOps Maturity as Business Capability")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(W/2, H - 100, "Each level is not a technology grade. It is a unit of compounding business value.")

    # Layout — concentric rings to the LEFT of center, descriptions to the right
    cx, cy = 540, 560
    # Three levels — innermost = most mature (Level 2), outermost = least mature (Level 0)
    # Innermost is the goal; outermost is where most enterprises start
    rings = [
        # (outer_r, fill_color, label, sub_label)
        (350, TAUPE,    "Level 0",   "Manual"),
        (260, BURGUNDY, "Level 1",   "Pipeline\nautomation"),
        (170, EMERALD,  "Level 2",   "Full ML\nautomation"),
    ]

    # Draw rings largest to smallest (so smaller ones overlay)
    for r, color, _, _ in rings:
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.circle(cx, cy, r, stroke=1, fill=1)

    # Labels on the rings — placed at the TOP of each ring band, in Ivory
    # Outermost ring label
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 350 - 38, "Level 0")
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(cx, cy + 350 - 60, "Manual")

    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 260 - 38, "Level 1")
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(cx, cy + 260 - 60, "Pipelined")

    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 20, "Level 2")
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(cx, cy - 5, "Full")
    c.drawCentredString(cx, cy - 25, "Automation")

    # Right-hand side description blocks aligned to rings
    desc_x = 1050
    desc_w = 480

    # Level 0 description (top)
    desc_blocks = [
        {
            "y": 880,
            "label": "Level 0 — Manual",
            "color": TAUPE,
            "lines": [
                "Scripts, notebooks, models on a laptop.",
                "Every change is a project. Most ML lives here.",
                "Business outcome: pilot purgatory.",
            ],
            "pct": "~85% of enterprises",
        },
        {
            "y": 600,
            "label": "Level 1 — Pipelined",
            "color": BURGUNDY,
            "lines": [
                "Automated retraining pipelines. Triggered",
                "by new data. Model improvement keeps",
                "pace with the world.",
            ],
            "pct": "AWS path: SageMaker Pipelines + Registry",
        },
        {
            "y": 280,
            "label": "Level 2 — Full Automation",
            "color": EMERALD,
            "lines": [
                "Pipelines themselves are version-controlled,",
                "owned by the org, not individual engineers.",
                "ML compounds across the enterprise.",
            ],
            "pct": "~6% of organizations — AI high performers",
        },
    ]

    for block in desc_blocks:
        # Title with color swatch
        c.setFillColor(block["color"])
        c.circle(desc_x + 15, block["y"] - 6, 10, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 18)
        c.drawString(desc_x + 38, block["y"] - 10, block["label"])

        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 14)
        for j, line in enumerate(block["lines"]):
            c.drawString(desc_x, block["y"] - 42 - j * 22, line)

        c.setFillColor(OCHRE)
        c.setFont('Poppins-Medium', 13)
        c.drawString(desc_x, block["y"] - 42 - len(block["lines"]) * 22 - 8, block["pct"])

    # Footer attribution
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(W/2, 40, "The gap between Level 0 and Level 1 is where most enterprise AI ROI is currently trapped.")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()

    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
